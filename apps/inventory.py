import os
import socket
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import JSONHandler, data_path, port, read_json, send_json


DB_PATH = data_path("inventory.db")
REDIS_HOST = os.environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "26379"))


def redis_command(*parts):
    chunks = ["*%d\r\n" % len(parts)]
    for part in parts:
        value = str(part).encode()
        chunks.extend(("$%d\r\n" % len(value), value, b"\r\n"))
    payload = b"".join(item.encode() if isinstance(item, str) else item for item in chunks)
    with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=2) as connection:
        connection.sendall(payload)
        response = connection.makefile("rb")
        prefix = response.read(1)
        value = response.readline().rstrip(b"\r\n").decode()
    if prefix == b":":
        return int(value)
    if prefix == b"+":
        return value
    raise RuntimeError(value)


def connect():
    return sqlite3.connect(DB_PATH)


def prepare():
    with connect() as database:
        database.execute(
            "CREATE TABLE IF NOT EXISTS stock "
            "(product_id INTEGER PRIMARY KEY, available INTEGER NOT NULL)"
        )
        database.execute(
            "CREATE TABLE IF NOT EXISTS reservations "
            "(id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL, quantity INTEGER NOT NULL, "
            "status TEXT NOT NULL)"
        )
        database.executemany(
            "INSERT OR IGNORE INTO stock (product_id, available) VALUES (?, ?)",
            [(1, 8), (2, 5)],
        )


def snapshot():
    with connect() as database:
        rows = database.execute(
            "SELECT product_id, available FROM stock ORDER BY product_id"
        ).fetchall()
    return [{"product_id": row[0], "available": row[1]} for row in rows]


def state():
    with connect() as database:
        rows = database.execute(
            "SELECT id, product_id, quantity, status "
            "FROM reservations ORDER BY id"
        ).fetchall()
    return {
        "stock": snapshot(),
        "reservations": [
            {
                "id": row[0],
                "product_id": row[1],
                "quantity": row[2],
                "status": row[3],
            }
            for row in rows
        ],
    }


def reserve(product_id, quantity):
    if quantity <= 0:
        return None, "quantity must be positive"
    with connect() as database:
        row = database.execute(
            "SELECT available FROM stock WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return None, "product not found"
        if row[0] < quantity:
            return None, "insufficient stock"
        reservation_id = redis_command("INCR", "orbit:demo:reservation")
        database.execute(
            "UPDATE stock SET available = available - ? WHERE product_id = ?",
            (quantity, product_id),
        )
        database.execute(
            "INSERT INTO reservations (id, product_id, quantity, status) VALUES (?, ?, ?, ?)",
            (reservation_id, product_id, quantity, "active"),
        )
    return {
        "id": reservation_id,
        "product_id": product_id,
        "quantity": quantity,
        "remaining": row[0] - quantity,
    }, None


def release(reservation_id):
    with connect() as database:
        row = database.execute(
            "SELECT product_id, quantity, status FROM reservations WHERE id = ?",
            (reservation_id,),
        ).fetchone()
        if row is None:
            return False, "reservation not found"
        if row[2] == "released":
            return True, None
        database.execute(
            "UPDATE stock SET available = available + ? WHERE product_id = ?",
            (row[1], row[0]),
        )
        database.execute(
            "UPDATE reservations SET status = 'released' WHERE id = ?",
            (reservation_id,),
        )
    return True, None


class Handler(JSONHandler, BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            redis_command("PING")
            send_json(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "service": "shop-inventory-api",
                    "database": "sqlite",
                    "redis": "connected",
                },
            )
            return
        if self.path == "/stock":
            send_json(self, HTTPStatus.OK, {"stock": snapshot()})
            return
        if self.path == "/state":
            send_json(self, HTTPStatus.OK, state())
            return
        send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/reservations/") and self.path.endswith("/release"):
            try:
                reservation_id = int(self.path.split("/")[2])
                released, problem = release(reservation_id)
            except ValueError:
                released, problem = False, "invalid reservation id"
            send_json(
                self,
                HTTPStatus.OK if released else HTTPStatus.NOT_FOUND,
                {"released": True, "id": reservation_id}
                if released
                else {"error": problem},
            )
            return
        if self.path != "/reservations":
            send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            payload = read_json(self)
            reservation, problem = reserve(
                int(payload.get("product_id", 0)),
                int(payload.get("quantity", 0)),
            )
        except (OSError, RuntimeError, TypeError, ValueError):
            send_json(self, HTTPStatus.SERVICE_UNAVAILABLE, {"error": "inventory unavailable"})
            return
        send_json(
            self,
            HTTPStatus.CREATED if reservation else HTTPStatus.CONFLICT,
            reservation or {"error": problem},
        )


if __name__ == "__main__":
    prepare()
    ThreadingHTTPServer(("127.0.0.1", port(28102)), Handler).serve_forever()
