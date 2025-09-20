import socket
from .BaseTransport import BaseTransport

class UdpTransport(BaseTransport):
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.host, self.port))
        print(f"UDP server listening on {self.host}:{self.port}")

        while True:
            data, addr = server_socket.recvfrom(self.server.BUFFER_SIZE)
            self.server.handle_client(UdpConnection(server_socket, addr, data))

class UdpConnection:
    def __init__(self, server_socket, addr, initial_data):
        self.server_socket = server_socket
        self.addr = addr
        self._initial_data = initial_data
        self._consumed = False

    def recv(self, buffer_size: int):
        if not self._consumed:
            self._consumed = True
            return self._initial_data
        data, _ = self.server_socket.recvfrom(buffer_size)
        return data

    def send(self, data: str):
        self.server_socket.sendto((data + "\n").encode(), self.addr)

    def close(self):
        # nothing to close for UDP
        pass
