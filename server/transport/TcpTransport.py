import socket
from .BaseTransport import BaseTransport

class TcpTransport(BaseTransport):
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        print(f"TCP server listening on {self.host}:{self.port}")

        while True:
            conn, addr = server_socket.accept()
            print(f"TCP connection with {addr}")
            self.server.handle_client(TcpConnection(conn, addr))

class TcpConnection:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr

    def recv(self, buffer_size: int):
        return self.conn.recv(buffer_size)

    def send(self, data: str):
        self.conn.sendall((data + "\n").encode())

    def close(self):
        self.conn.close()
