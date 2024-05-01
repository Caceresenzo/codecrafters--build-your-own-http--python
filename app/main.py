import socket


def main():
    print("codecrafters build-your-own-http")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    client, _ = server_socket.accept()
    io = socket.SocketIO(client, "rw")

    request_line = io.readline()[:-2].decode("ascii")
    parts = request_line.split(" ")
    method, path, version = parts

    if path == "/":
        client.send(b"HTTP/1.1 200 OK\r\n\r\n")
    else:
        client.send(b"HTTP/1.1 404 Not Found\r\n\r\n")

    client.close()

if __name__ == "__main__":
    main()
