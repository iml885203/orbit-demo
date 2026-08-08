import os
import socket
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import JSONHandler, port, read_json, send_json


REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "26379"))
INITIAL_STOCK = {1: 5, 2: 3}

# One lock serialises check-then-decrement so concurrent buys cannot oversell.
LOCK = threading.Lock()


def redis_command(*parts):
    """Send one Redis command over a fresh socket and return its reply.

    The demo speaks the Redis protocol (RESP) directly so it needs no
    third-party client library — the whole repo runs on the Python
    standard library alone.
    """
    message = b"*%d\r\n" % len(parts)
    for part in parts:
        chunk = str(part).encode()
        message += b"$%d\r\n%s\r\n" % (len(chunk), chunk)
    with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=2) as connection:
        connection.sendall(message)
        reply = connection.makefile("rb")
        kind = reply.read(1)
        value = reply.readline().rstrip(b"\r\n").decode()
        if kind == b":":
            return int(value)
        if kind == b"+":
            return value
        if kind == b"$":
            if value == "-1":
                return None
            return reply.read(int(value)).decode()
        raise RuntimeError(value)


def available(product_id):
    value = redis_command("GET", "stock:%d" % product_id)
    if value is None:
        # A freshly created Redis container starts empty; seed it lazily so
        # the demo also recovers from a recreated container.
        redis_command("SET", "stock:%d" % product_id, INITIAL_STOCK[product_id], "NX")
        value = redis_command("GET", "stock:%d" % product_id)
    return int(value)


def stock():
    return [
        {"product_id": product_id, "available": available(product_id)}
        for product_id in sorted(INITIAL_STOCK)
    ]


def take(product_id, quantity):
    if quantity <= 0:
        return HTTPStatus.CONFLICT, {"error": "quantity must be positive"}
    if product_id not in INITIAL_STOCK:
        return HTTPStatus.NOT_FOUND, {"error": "product not found"}
    with LOCK:
        if available(product_id) < quantity:
            return HTTPStatus.CONFLICT, {"error": "insufficient stock"}
        remaining = redis_command("DECRBY", "stock:%d" % product_id, quantity)
    return HTTPStatus.OK, {"product_id": product_id, "taken": quantity, "remaining": remaining}


def restock():
    for product_id, quantity in INITIAL_STOCK.items():
        redis_command("SET", "stock:%d" % product_id, quantity)


class Handler(JSONHandler, BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            try:
                redis_command("PING")
            except OSError:
                send_json(
                    self,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"ok": False, "service": "shop-inventory-api", "error": "redis is unreachable"},
                )
                return
            send_json(
                self,
                HTTPStatus.OK,
                {"ok": True, "service": "shop-inventory-api", "store": "redis"},
            )
            return
        if self.path == "/stock":
            send_json(self, HTTPStatus.OK, {"stock": stock()})
            return
        send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self):
        try:
            if self.path == "/restock":
                restock()
                send_json(self, HTTPStatus.OK, {"stock": stock()})
                return
            if self.path == "/take":
                payload = read_json(self)
                status, result = take(
                    int(payload.get("product_id", 0)),
                    int(payload.get("quantity", 0)),
                )
                send_json(self, status, result)
                return
        except (OSError, RuntimeError, TypeError, ValueError):
            send_json(self, HTTPStatus.SERVICE_UNAVAILABLE, {"error": "inventory unavailable"})
            return
        send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", port(28102)), Handler).serve_forever()
