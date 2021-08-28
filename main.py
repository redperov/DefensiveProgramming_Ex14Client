from client import Client

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5000

    client = Client(host, port)
    client.start()

