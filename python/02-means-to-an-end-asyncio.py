import asyncio
import socket
import struct
from dataclasses import dataclass
from enum import Enum
from sys import stdout
from typing import AsyncGenerator

from fastsocket import get_ip

HOST = "::"
PORT = 6969
CHUNK_SIZE = 4096


class RequestType(Enum):
    INSERT = b"I"
    QUERY = b"Q"


@dataclass
class Request:
    # ! = network byte order, c = char, i = int
    FORMAT = "!cii"
    SIZE = struct.calcsize(FORMAT)

    type: RequestType
    first: int
    second: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "Request":
        if len(data) != cls.SIZE:
            raise ValueError("Invalid message size")
        raw_type, first, second = struct.unpack(cls.FORMAT, data)
        try:
            msg_type = RequestType(raw_type)
        except ValueError:
            raise ValueError(f"Unknown message type: {raw_type!r}")
        return cls(msg_type, first, second)


@dataclass
class Response:
    FORMAT = "!i"
    SIZE = struct.calcsize(FORMAT)

    value: int

    def to_bytes(self) -> bytes:
        return struct.pack(self.FORMAT, self.value)


async def parse_requests(reader: asyncio.StreamReader) -> AsyncGenerator[Request]:
    data = bytes()
    while True:
        chunk = await reader.read(CHUNK_SIZE)
        if not chunk:
            break
        data += chunk

        while len(data) >= Request.SIZE:
            request_bytes = data[: Request.SIZE]
            try:
                yield Request.from_bytes(request_bytes)
            except ValueError:
                print(f"Bad Request: {request_bytes.hex()}")
            data = data[Request.SIZE :]


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    print = stdout.write
    addr = writer.get_extra_info("peername")
    print(f"Connection from {addr}\n")
    store = {}

    async for request in parse_requests(reader):
        print(f"<-- {request.type} {request.first} {request.second}\n")
        match request.type:
            case RequestType.INSERT:
                timestamp, price = request.first, request.second
                store[timestamp] = price
            case RequestType.QUERY:
                mintime, maxtime = request.first, request.second
                total = count = 0
                for timestamp, price in store.items():
                    if mintime <= timestamp <= maxtime:
                        total += price
                        count += 1
                mean = int(total / count if count else 0)
                print(f"--> {mean}\n")
                writer.write(Response(value=mean).to_bytes())
                await writer.drain()

    print(f"Closed connection from {addr}\n")
    writer.close()
    await writer.wait_closed()


async def main():
    # Create a dual-stack socket that listens on all interfaces.
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.setblocking(False)
    sock.bind((HOST, PORT))
    sock.listen()

    print(f"Listening on {PORT} at")
    for ip in get_ip():
        print(f"  => {ip}")

    server = await asyncio.start_server(handle, sock=sock)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("bye.")
