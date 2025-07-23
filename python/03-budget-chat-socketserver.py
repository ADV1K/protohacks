import socket
import socketserver
from dataclasses import dataclass
from typing import Generator
from uuid import UUID, uuid4

from fastsocket import get_ip

HOST = "::"
PORT = 6969
CHUNK_SIZE = 4096


@dataclass(eq=True, frozen=True, unsafe_hash=True)
class User:
    id: UUID
    name: str
    socket: socket.socket


class BudgetChatServer(socketserver.BaseRequestHandler):
    user: User
    users: list[User] = []
    data: str = ""

    def setup(self) -> None:
        print("Connected from", self.client_address)

        # Welcome message, ask for name
        self.request.sendall(b"Welcome to budgetchat! What shall I call you?\n")
        username = self.read_message()

        # User disconnected before sending name
        if username is None:
            return
        self.user = User(uuid4(), username, self.request)

        # only allow alphanumeric characters and don't allow empty names
        if not self.user.name.isalnum():
            self.request.sendall(b"Illegal Name!\n")
            self.finish()
            return

        # This room contains...
        online_users = ", ".join(user.name for user in self.users)
        self.request.sendall(f"* The room contains: {online_users}\n".encode())

        # Tell everyone else that user has joined
        self.users.append(self.user)
        self.broadcast(f"* {self.user.name} has entered the room")

    def handle(self) -> None:
        for message in self.read_messages():
            print(f"<-- [{self.user.name}] {message}")
            self.broadcast(f"[{self.user.name}] {message}")

    def read_messages(self, delimiter: str = "\n") -> Generator[str]:
        while True:
            try:
                message = self.read_message(delimiter)
            except OSError:  # socket closed
                return
            if message is None:  # client disconnected
                break
            yield message

    def read_message(self, delimiter: str = "\n") -> str | None:
        while delimiter not in self.data:
            chunk = self.request.recv(CHUNK_SIZE).decode("utf-8")
            if not chunk:  # client disconnected
                return None
            self.data += chunk

        message, _, self.data = self.data.partition(delimiter)
        return message.strip()

    def broadcast(self, message: str):
        encoded_message = (message + "\n").encode()
        for user in self.users:
            if user is self.user:  # don't send to self lol
                continue

            user.socket.sendall(encoded_message)

    def finish(self) -> None:
        # If user is in the room, remove them
        if hasattr(self, "user") and self.user in self.users:
            self.broadcast(f"* {self.user.name} has left the room")
            self.users.remove(self.user)
            print("Disconnected from", self.user.name, self.client_address)
        else:
            print("Disconnected from", self.client_address)
        self.request.close()


if __name__ == "__main__":
    socketserver.TCPServer.address_family = socket.AF_INET6
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer((HOST, PORT), BudgetChatServer)

    print(f"Listening on {PORT} at")
    for ip in get_ip():
        print(f"  => {ip}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("bye.")
        server.server_close()
