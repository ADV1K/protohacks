import socket
import socketserver
import struct
from sys import stdout
from typing import Generator

from fastsocket import get_ip

HOST = "::"
PORT = 6969
CHUNK_SIZE = 4096

INCOMING_MESSAGE_FORMAT = "!cii"  # ! = network byte order, c = char, i = int
OUTGOING_MESSAGE_FORMAT = "!i"
INCOMING_MESSAGE_SIZE = struct.calcsize(INCOMING_MESSAGE_FORMAT)


class MessageType:
    INSERT = b"I"
    QUERY = b"Q"


class TimeseriesDatabaseServer(socketserver.BaseRequestHandler):
    def setup(self) -> None:
        stdout.write(f"Connected from {self.client_address}\n")
        self.db = {}

    def handle(self) -> None:
        for message in self.read_messages():
            message_type, num1, num2 = struct.unpack(INCOMING_MESSAGE_FORMAT, message)
            stdout.write(f"<-- {message_type} {num1} {num2}\n")
            match message_type:
                case MessageType.INSERT:
                    self.handle_insert(num1, num2)
                case MessageType.QUERY:
                    self.handle_query(num1, num2)

    def handle_insert(self, timestamp: int, price: int) -> None:
        self.db[timestamp] = price

    def handle_query(self, mintime: int, maxtime: int) -> None:
        total = count = 0
        for timestamp, price in self.db.items():
            if mintime <= timestamp <= maxtime:
                total += price
                count += 1
        mean = int(total / count if count else 0)
        stdout.write(f"--> {mean}\n")
        self.request.sendall(struct.pack(OUTGOING_MESSAGE_FORMAT, mean))

    def read_messages(self) -> Generator[bytes]:
        data = b""
        while True:
            data += self.request.recv(CHUNK_SIZE)
            if not data:  # client disconnected
                break

            while len(data) >= INCOMING_MESSAGE_SIZE:
                message = data[:INCOMING_MESSAGE_SIZE]
                data = data[INCOMING_MESSAGE_SIZE:]
                yield message

    def finish(self) -> None:
        stdout.write(f"Disconnected from {self.client_address}\n")
        self.request.close()


if __name__ == "__main__":
    socketserver.TCPServer.address_family = socket.AF_INET6
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer((HOST, PORT), TimeseriesDatabaseServer)

    print(f"Listening on {PORT} at")
    for ip in get_ip():
        print(f"  => {ip}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("bye.")
        server.server_close()
