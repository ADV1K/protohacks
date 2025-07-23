import socket
import socketserver

from fastsocket import get_ip

HOST = "::"
PORT = 6969


class EchoServer(socketserver.BaseRequestHandler):
    def handle(self):
        print("Connected from", self.client_address)
        while True:
            data = self.request.recv(1024)
            if not data:  # client disconnected
                break
            self.request.send(data)


if __name__ == "__main__":
    socketserver.TCPServer.address_family = socket.AF_INET6
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer((HOST, PORT), EchoServer)

    print(f"Listening on {PORT} at")
    for ip in get_ip():
        print(f"  => {ip}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("bye.")
        server.server_close()
