import socketserver
import socket
import time

HOST = ""
PORT = 6969

DATABASE = {"version": "Advik's UDP KV Store v0.0.1"}
IMMUTABLE_KEYS = ("version",)


class UDPHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        message, sock = self.request
        message = message.decode("utf-8")
        key, _, value = message.partition("=")
        print(f"<-- {message} [{self.client_address[0]}]:{self.client_address[1]}")

        # Insert
        if "=" in message:
            if key not in IMMUTABLE_KEYS:
                DATABASE[key] = value

        # Retrieve
        else:
            value = DATABASE.get(key, "")
            response = f"{key}={value}"
            sock.sendto(response.encode("utf-8"), self.client_address)
            print(f"--> {response} [{self.client_address[0]}]:{self.client_address[1]}")


if __name__ == "__main__":
    socketserver.UDPServer.address_family = socket.AF_INET6
    socketserver.UDPServer.max_packet_size = 1000
    socketserver.UDPServer.allow_reuse_address = True
    server = socketserver.ThreadingUDPServer((HOST, PORT), UDPHandler)

    try:
        print(f"Listening on {server.server_address}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server is shutting down...")

        server.server_close()
