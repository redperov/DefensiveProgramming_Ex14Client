from client import Client

if __name__ == "__main__":

    # TODO move to file
    host = "127.0.0.1"
    port = 5000

    # Run client
    client = Client(host, port)
    client.start()

