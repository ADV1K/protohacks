import socketserver
import socket

HOST = ""
PORT = 6969


class TCPEchoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("Connected from", self.client_address)
        while True:
            data = self.request.recv(1024)
            if not data:  # client disconnected
                break
            self.request.send(data)


# class TCPServer(socketserver.TCPServer):
#     def __init__(self, server_address, handler_class):
#         super().__init__(server_address, handler_class, bind_and_activate=False)
#
#         # Create a dual-stack socket, with IPv6 preference
#         self.socket = socket.create_server(server_address, family=socket.AF_INET6, dualstack_ipv6=True)
#         print("Listening on {}".format(self.socket.getsockname()))
#
#         # listen for incoming connections
#         try:
#             self.server_activate()
#         except OSError:
#             self.server_close()
#             raise


if __name__ == "__main__":
    socketserver.TCPServer.address_family = socket.AF_INET6
    server = socketserver.TCPServer((HOST, PORT), TCPEchoHandler)

    try:
        print("Listening on {}".format(server.server_address))
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server is shutting down...")
        server.server_close()
