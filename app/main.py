import os
import socket
import sys

STATUS_PHRASES = {
    200: "OK",
    201: "Created",
    404: "Not Found"
}


def gzip(input: bytes):
    pass


def main():
    print("codecrafters build-your-own-http")

    directory = None
    if len(sys.argv) == 3:
        directory = sys.argv[2]
        os.chdir(directory)

    server = socket.create_server(("0.0.0.0", 4221), reuse_port=True)
    while True:
        client, addr = server.accept()

        print("connected", addr)

        pid = os.fork()
        if pid:
            client.close()
            continue

        io = socket.SocketIO(client, "rw")

        request_line = io.readline()[:-2].decode("ascii")
        parts = request_line.split(" ")
        method, path, version = parts

        headers = {}
        while line := io.readline()[:-2].decode("ascii"):
            key, value = line.split(": ")
            headers[key.lower()] = value

        body = None
        if is_post := (method == "POST"):
            content_length = int(headers.get("Content-Length".lower(), 0))
            body = io.read(content_length)

        if path == "/":
            response = 200, {}, None
        elif path.startswith("/echo/"):
            message = path[6:]

            response = (
                200,
                {
                    "Content-Type": "text/plain",
                },
                message.encode("ascii")
            )
        elif path == "/user-agent":
            message = headers["User-Agent".lower()]

            response = (
                200,
                {
                    "Content-Type": "text/plain",
                },
                message.encode("ascii")
            )
        elif path.startswith("/files/"):
            name = path[7:]

            if is_post:
                parent = os.path.dirname(name)
                if parent:
                    os.makedirs(parent, exist_ok=True)

                with open(name, "wb") as fd:
                    fd.write(body)

                response = 201, {}, None
            elif os.path.exists(name):
                with open(name, "rb") as fd:
                    content = fd.read()

                response = (
                    200,
                    {
                        "Content-Type": "application/octet-stream",
                    },
                    content
                )
            else:
                response = 404, {}, None
        else:
            response = 404, {}, None

        status, response_headers, body = response
        phrase = STATUS_PHRASES[status]

        accept_encoding: str = headers.get("Accept-Encoding".lower(), "")
        encoder = None
        for name in accept_encoding.split(","):
            name = name.strip()

            if name == "gzip":
                encoder = gzip
                break

        if encoder is not None:
            response_headers["Content-Encoding"] = encoder.__name__

        client.send(f"HTTP/1.1 {status} {phrase}\r\n".encode("ascii"))

        for key, value in response_headers.items():
            client.send(f"{key}: {value}\r\n".encode("ascii"))

        if body is not None:
            size = len(body)
            client.send(f"Content-Length: {size}\r\n".encode("ascii"))

        client.send(b"\r\n")

        if body is not None:
            client.send(body)

        client.close()
        exit(0)


if __name__ == "__main__":
    main()
