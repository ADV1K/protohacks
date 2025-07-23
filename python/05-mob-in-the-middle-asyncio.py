import asyncio
import re
import socket
from typing import AsyncGenerator, Awaitable, Callable

from fastsocket import get_ip

HOST = "::"
PORT = 6969
UPSTREAM_SERVER = ("chat.protohackers.com", 16963)
CHUNK_SIZE = 4096
MESSAGE_SEPARATOR = b"\n"
BOGUSCOIN_RE = re.compile(r"(^|\s)7[a-zA-Z0-9]{25,34}(?=\s|$)")
TONY_ADDRESS = "7YWHMfk9JZe0LM0g1ZauHuiSxhI"


async def handle(
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
) -> None:
    addr = client_writer.get_extra_info("peername")[0]
    print(f"Client Connected: {addr}")

    upstream_reader, upstream_writer = await asyncio.open_connection(*UPSTREAM_SERVER)
    await asyncio.gather(
        forward(client_reader, upstream_writer, transform, "client -> server"),
        forward(upstream_reader, client_writer, transform, "server -> client"),
    )

    print(f"Client Disconnected: {addr}")
    client_writer.close()
    await client_writer.wait_closed()


async def forward(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    transform: Callable[[bytes], Awaitable[bytes]],
    label: str,
):
    try:
        async for request in parse_requests(reader):
            print(f"{label}: {request}")
            writer.write(await transform(request))
            writer.write(b"\n")
            await writer.drain()
    except Exception:
        pass

    writer.close()
    await writer.wait_closed()


async def transform(text: bytes) -> bytes:
    return BOGUSCOIN_RE.sub(lambda m: m.group(1) + TONY_ADDRESS, text.decode()).encode()


async def parse_requests(reader: asyncio.StreamReader) -> AsyncGenerator[bytes]:
    data = bytes()
    while True:
        chunk = await reader.read(CHUNK_SIZE)
        if not chunk:
            break
        data += chunk

        while MESSAGE_SEPARATOR in data:
            message, data = data.split(MESSAGE_SEPARATOR)
            yield message


async def main() -> None:
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
