import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    s.connect(("127.0.0.1",65432))
    while True:
        s.sendall(input('>> ').encode())
        response = s.recv(128).decode(errors="ignore")
        print(response)
except Exception as e:
    print(e)
    s.close()

