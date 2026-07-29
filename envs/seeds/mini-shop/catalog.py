import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import JSONHandler, data_path, port, send_json


DB_PATH = data_path("catalog.db")
PRODUCTS = [
    (1, "Orbit Mug", "A quiet reminder that every service is healthy.", 18),
    (2, "Local Dev Hoodie", "Host processes and containers, comfortably together.", 52),
]


def connect():
    return sqlite3.connect(DB_PATH)


def prepare():
    with connect() as database:
        database.execute(
            "CREATE TABLE IF NOT EXISTS products "
            "(id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL, price INTEGER NOT NULL)"
        )
        database.executemany(
            "INSERT OR REPLACE INTO products (id, name, description, price) VALUES (?, ?, ?, ?)",
            PRODUCTS,
        )


def products():
    with connect() as database:
        rows = database.execute(
            "SELECT id, name, description, price FROM products ORDER BY id"
        ).fetchall()
    return [
        {"id": row[0], "name": row[1], "description": row[2], "price": row[3]}
        for row in rows
    ]


class Handler(JSONHandler, BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            send_json(
                self,
                HTTPStatus.OK,
                {"ok": True, "service": "shop-catalog-api", "database": "sqlite"},
            )
            return
        if self.path == "/products":
            send_json(self, HTTPStatus.OK, {"products": products()})
            return
        if self.path.startswith("/products/"):
            try:
                product_id = int(self.path.rsplit("/", 1)[1])
            except ValueError:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": "invalid product id"})
                return
            product = next((item for item in products() if item["id"] == product_id), None)
            send_json(
                self,
                HTTPStatus.OK if product else HTTPStatus.NOT_FOUND,
                product or {"error": "product not found"},
            )
            return
        send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})


if __name__ == "__main__":
    prepare()
    ThreadingHTTPServer(("127.0.0.1", port(28101)), Handler).serve_forever()
