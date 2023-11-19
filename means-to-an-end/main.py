from sys import stdout
import socketserver
import socket
import struct

HOST = ""
PORT = 6969

INCOMING_MESSAGE_FORMAT = "!cii"  # ! = network byte order, c = char, i = int
OUTGOING_MESSAGE_FORMAT = "!i"
INCOMING_MESSAGE_SIZE = struct.calcsize(INCOMING_MESSAGE_FORMAT)

print = stdout.write  # because print() is too slow for one of the tests


class MessageType:
    INSERT = b"I"
    QUERY = b"Q"


class TCPHandler(socketserver.BaseRequestHandler):
    def setup(self) -> None:
        print(f"Connected from {self.client_address}\n")
        self.db = {}

    def handle(self) -> None:
        for message in self.read_messages():
            message_type, num1, num2 = struct.unpack(INCOMING_MESSAGE_FORMAT, message)
            print(f"<-- {message_type} {num1} {num2}\n")
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
        print(f"--> {mean}\n")
        self.request.sendall(struct.pack(OUTGOING_MESSAGE_FORMAT, mean))

    def read_messages(self) -> bytes:
        data = b""
        while True:
            data += self.request.recv(1024)
            if not data:  # client disconnected
                break

            while len(data) >= INCOMING_MESSAGE_SIZE:
                message = data[:INCOMING_MESSAGE_SIZE]
                data = data[INCOMING_MESSAGE_SIZE:]
                yield message

    def finish(self) -> None:
        print(f"Disconnected from {self.client_address}\n")
        self.request.close()


if __name__ == "__main__":
    socketserver.TCPServer.address_family = socket.AF_INET6
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer((HOST, PORT), TCPHandler)

    try:
        print(f"Listening on {server.server_address}\n")
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server is shutting down...")
        server.server_close()
