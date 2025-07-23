import json
import socket
import socketserver
from dataclasses import dataclass, fields
from typing import Generator

from fastsocket import get_ip

HOST = "::"
PORT = 6969
CHUNK_SIZE = 4096


@dataclass
class DataIn:
    method: str
    number: int | float

    @classmethod
    def deserialize(cls, json_data):
        f = set(f.name for f in fields(cls))
        return cls(**{k: v for k, v in json.loads(json_data).items() if k in f})

    def __post_init__(self):
        if self.method != "isPrime":
            raise ValueError(f"Invalid method: {self.method}")
        if not isinstance(self.number, (int, float)) or isinstance(self.number, bool):
            raise ValueError(f"Invalid number: {self.number}")


@dataclass
class DataOut:
    prime: bool
    method: str = "isPrime"

    def serialize(self):
        return json.dumps(self.__dict__) + "\n"


class PrimeTimeServer(socketserver.BaseRequestHandler):
    def setup(self) -> None:
        print("Connected from", self.client_address)

    def handle(self) -> None:
        for message in self.read_messages():
            try:
                data_in = DataIn.deserialize(message)
            except (json.JSONDecodeError, ValueError, TypeError):
                self.send_message("Invalid Request\n")
            else:
                data_out = DataOut(prime=is_prime(data_in.number)).serialize()
                self.send_message(data_out)

    def read_messages(self, delimiter: str = "\n") -> Generator[str]:
        data = ""
        while True:
            data += self.request.recv(CHUNK_SIZE).decode("utf-8")
            if not data:  # client disconnected
                break

            while delimiter in data:
                message, data = data.split(delimiter, 1)
                print("<-- ", message)
                yield message

    def send_message(self, message: str):
        print("--> ", message.strip())
        self.request.sendall(message.encode())

    def finish(self) -> None:
        print("Disconnected from", self.client_address)
        self.request.close()


def is_prime(number):
    # It works by looking at all numbers of the form 6k ± 1, up to sqrt(n), where k is any integer.
    # Or you can just use the following regex if you're a masochist:
    # https://web.archive.org/web/20220513113609/neilk.net/blog/2000/06/01/abigails-regex-to-test-for-prime-numbers/

    if number <= 1 or int(number) != number:
        return False
    elif number in (2, 3):
        return True
    elif number % 2 == 0 or number % 3 == 0:
        return False

    for i in range(6, int(number**0.5) + 2, 6):
        if number % (i - 1) == 0 or number % (i + 1) == 0:
            return False

    return True


if __name__ == "__main__":
    socketserver.TCPServer.address_family = socket.AF_INET6
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer((HOST, PORT), PrimeTimeServer)

    print(f"Listening on {PORT} at")
    for ip in get_ip():
        print(f"  => {ip}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("bye.")
        server.server_close()
