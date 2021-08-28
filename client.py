import socket


class Client:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.server_host, self.server_port))
            s.sendall(b"A" * 5000000)
            print("Message sent")
            data = s.recv(1024)
        print('Received', repr(data))
