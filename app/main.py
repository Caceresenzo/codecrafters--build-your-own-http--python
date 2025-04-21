import dataclasses
import enum
import os
import socket
import sys


class Method(enum.Enum):
    GET = "GET"
    POST = "POST"


@dataclasses.dataclass
class Request:
    method: Method
    path: str
    headers: dict[str, str]
    body: bytes | None = None


class Status(enum.Enum):
    OK = "200 OK"
    CREATED = "201 Created"
    NOT_FOUND = "404 Not Found"


@dataclasses.dataclass
class Response:
    status: Status
    headers: dict[str, str] = dataclasses.field(default_factory=dict)
    body: bytes | None = None


def gzip(input: bytes):
    import gzip
    return gzip.compress(input)


def exchange(client: socket.socket):
    io = socket.SocketIO(client, "rw")

    def parse_request() -> Request | None:
        request_line = io.readline()[:-2].decode("ascii")

        if not len(request_line):
            return None

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

        return Request(
            Method.POST if is_post else Method.GET,
            path,
            headers,
            body
        )

    def route(request: Request) -> Response:
        if request.path == "/":
            return Response(Status.OK)

        elif request.path.startswith("/echo/"):
            message = request.path[6:]

            return Response(
                Status.OK,
                {
                    "Content-Type": "text/plain",
                },
                message.encode("ascii")
            )

        elif request.path == "/user-agent":
            message = request.headers["User-Agent".lower()]

            return Response(
                Status.OK,
                {
                    "Content-Type": "text/plain",
                },
                message.encode("ascii")
            )

        elif request.path.startswith("/files/"):
            name = request.path[7:]

            if request.method == Method.POST:
                parent = os.path.dirname(name)
                if parent:
                    os.makedirs(parent, exist_ok=True)

                with open(name, "wb") as fd:
                    fd.write(request.body)

                return Response(Status.CREATED)

            elif os.path.exists(name):
                with open(name, "rb") as fd:
                    content = fd.read()

                return Response(
                    Status.OK,
                    {
                        "Content-Type": "application/octet-stream",
                    },
                    content
                )

        return Response(Status.NOT_FOUND)

    def compress(request: Request, response: Response) -> Response:
        accept_encoding: str = request.headers.get("Accept-Encoding".lower(), "")

        encoder = None
        for name in accept_encoding.split(","):
            name = name.strip()

            if name == "gzip":
                encoder = gzip
                break

        if encoder is not None:
            response.headers["Content-Encoding"] = encoder.__name__
            response.body = encoder(response.body)

        return response

    def connection(request: Request, response: Response) -> Response:
        connection = request.headers.get("Connection".lower())

        if close_after := connection == "close":
            response.headers["Connection"] = "close"

        return response, close_after

    def write_response(response: Response):
        client.send(f"HTTP/1.1 {response.status.value}\r\n".encode("ascii"))

        response.headers["Content-Length"] = str(len(response.body)) if response.body else "0"

        for key, value in response.headers.items():
            client.send(f"{key}: {value}\r\n".encode("ascii"))

        client.send(b"\r\n")

        if response.body is not None:
            client.send(response.body)

    while True:
        request = parse_request()
        if request is None:
            break
        
        response = route(request)
        response = compress(request, response)
        response, close_after = connection(request, response)
        write_response(response)

        if close_after:
            break


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

        exchange(client)

        client.close()
        exit(0)


if __name__ == "__main__":
    main()
