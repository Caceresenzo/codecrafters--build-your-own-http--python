import os
import socket


def main():
    print("codecrafters build-your-own-http")

    server = socket.create_server(("0.0.0.0", 4221), reuse_port=True)
    while True:
        client, addr = server.accept()

        print("connected", addr)

        pid = os.fork()
        if pid:
            continue

        io = socket.SocketIO(client, "rw")

        request_line = io.readline()[:-2].decode("ascii")
        parts = request_line.split(" ")
        method, path, version = parts

        headers = {}
        while line := io.readline()[:-2].decode("ascii"):
            key, value = line.split(": ")
            headers[key.lower()] = value

        if path == "/":
            client.send(b"HTTP/1.1 200 OK\r\n\r\n")
        elif path.startswith("/echo/"):
            message = path[6:]
            client.send(b"HTTP/1.1 200 OK\r\n")
            client.send(b"Content-Type: text/plain\r\n")
            client.send(f"Content-Length: {len(message)}\r\n".encode("ascii"))
            client.send(b"\r\n")
            client.send(message.encode("ascii"))
        elif path == "/user-agent":
            message = headers["User-Agent".lower()]
            client.send(b"HTTP/1.1 200 OK\r\n")
            client.send(b"Content-Type: text/plain\r\n")
            client.send(f"Content-Length: {len(message)}\r\n".encode("ascii"))
            client.send(b"\r\n")
            client.send(message.encode("ascii"))
        else:
            client.send(b"HTTP/1.1 404 Not Found\r\n\r\n")

        client.close()
        exit(0)

if __name__ == "__main__":
    main()
