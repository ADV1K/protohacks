import asyncio
import inspect
import socket
from typing import Callable

HOST = "::"
PORT = 9001
CHUNK_SIZE = 4096


"""
FLOW:
Start a tcp asyncio server
accept a connection

parse request, using either size or delimiter, and from_bytes
response = handler(request)
send response, encode using to_bytes

FUTURE SCOPE:
1. use a serialization library like msgspec
"""


class FastTCP:
    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port

    def handler(
        self,
        model,
        request_size: int | None = None,
        request_delimiter: bytes | None = None,
    ):
        def decorator(func: Callable):
            self.handler_func = func
            sig = inspect.signature(func)
            self.request_type = sig.parameters[
                list(sig.parameters.keys())[0]
            ].annotation
            self.response_type = sig.return_annotation

            if not (request_size or request_delimiter):
                raise Exception("One of size or delimiter is required")

            self.request_size = request_size
            self.request_delimiter = request_delimiter

            return func

        return decorator

    def parser(self) -> Callable: ...

    def run(self):
        try:
            asyncio.run(self._start_server())
        except KeyboardInterrupt:
            print("bye.")

    async def _start_server(self):
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        sock.setblocking(False)
        sock.bind((self.host, self.port))
        sock.listen()

        print(f"Listening on {self.port} at")
        for ip in get_ip():
            print(f"  => {ip}")

        server = await asyncio.start_server(self._handle_connection, sock=sock)
        async with server:
            await server.serve_forever()

    async def _handle_connection(self, reader, writer):
        addr = writer.get_extra_info("peername")
        print(f"Connection from {addr}\n")

        async for request in self._parse_requests(reader):
            response = await self.handler_func(request)
            writer.write(response.to_bytes())
            await writer.drain()

        print(f"Closed connection from {addr}\n")
        writer.close()
        await writer.wait_closed()

    async def _parse_requests(self, reader: asyncio.StreamReader):
        data = bytes()
        while True:
            chunk = await reader.read(CHUNK_SIZE)
            if not chunk:
                break
            data += chunk

            if self.request_size:
                while len(data) >= self.request_size:
                    request_bytes = data[: self.request_size]
                    try:
                        yield self.request_type.from_bytes(request_bytes)
                    except ValueError as e:
                        print(f"Error parsing request: {e!r}")
                    data = data[self.request_size :]
            elif self.request_delimiter:
                # Delimiter-based protocol
                while self.request_delimiter in data:
                    request_bytes, data = data.split(self.request_delimiter, 1)
                    try:
                        yield self.request_type.from_bytes(request_bytes)
                    except ValueError as e:
                        print(f"Error parsing request: {e!r}")
