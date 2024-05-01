import socket


def main():
    print("codecrafters build-your-own-http")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    client, _ = server_socket.accept()
    client.send(b"HTTP/1.1 200 OK\r\n\r\n")
    client.close()

if __name__ == "__main__":
    main()
