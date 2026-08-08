import os
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import JSONHandler, data_path, get_json, port, post_json, read_json, send_json


DB_PATH = data_path("orders.db")
CATALOG_URL = os.environ.get("SHOP_CATALOG_API_URL", "http://127.0.0.1:28101")
INVENTORY_URL = os.environ.get("SHOP_INVENTORY_API_URL", "http://127.0.0.1:28102")


def connect():
    return sqlite3.connect(DB_PATH)


def prepare():
    with connect() as database:
        database.execute(
            "CREATE TABLE IF NOT EXISTS orders "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL, "
            "product_name TEXT NOT NULL, quantity INTEGER NOT NULL, total INTEGER NOT NULL)"
        )


def orders():
    with connect() as database:
        rows = database.execute(
            "SELECT id, product_id, product_name, quantity, total FROM orders ORDER BY id"
        ).fetchall()
    return [
        {
            "id": row[0],
            "product_id": row[1],
            "product_name": row[2],
            "quantity": row[3],
            "total": row[4],
        }
        for row in rows
    ]


def checkout(product_id, quantity):
    product = get_json("%s/products/%d" % (CATALOG_URL, product_id))
    status, taken = post_json(
        INVENTORY_URL + "/take",
        {"product_id": product_id, "quantity": quantity},
    )
    if status != HTTPStatus.OK:
        return status, taken
    total = product["price"] * quantity
    with connect() as database:
        cursor = database.execute(
            "INSERT INTO orders (product_id, product_name, quantity, total) "
            "VALUES (?, ?, ?, ?)",
            (product_id, product["name"], quantity, total),
        )
        order_id = cursor.lastrowid
    return HTTPStatus.CREATED, {
        "id": order_id,
        "product": product,
        "quantity": quantity,
        "total": total,
        "remaining": taken["remaining"],
    }


class Handler(JSONHandler, BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            try:
                catalog = get_json(CATALOG_URL + "/health")
                inventory = get_json(INVENTORY_URL + "/health")
            except OSError:
                send_json(
                    self,
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"ok": False, "service": "shop-order-api", "error": "a dependency is unreachable"},
                )
                return
            send_json(
                self,
                HTTPStatus.OK,
                {
                    "ok": catalog["ok"] and inventory["ok"],
                    "service": "shop-order-api",
                    "database": "sqlite",
                },
            )
            return
        if self.path == "/orders":
            send_json(self, HTTPStatus.OK, {"orders": orders()})
            return
        send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self):
        if self.path != "/checkout":
            send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            payload = read_json(self)
            status, order = checkout(
                int(payload.get("product_id", 0)),
                int(payload.get("quantity", 0)),
            )
        except (OSError, sqlite3.Error, TypeError, ValueError):
            send_json(self, HTTPStatus.SERVICE_UNAVAILABLE, {"error": "checkout unavailable"})
            return
        send_json(self, status, order)


if __name__ == "__main__":
    prepare()
    ThreadingHTTPServer(("127.0.0.1", port(28103)), Handler).serve_forever()
