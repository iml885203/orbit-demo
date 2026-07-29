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
            "product_name TEXT NOT NULL, quantity INTEGER NOT NULL, total INTEGER NOT NULL, "
            "reservation_id INTEGER NOT NULL, status TEXT NOT NULL)"
        )


def create_order(product_id, quantity):
    product = get_json("%s/products/%d" % (CATALOG_URL, product_id))
    status, reservation = post_json(
        INVENTORY_URL + "/reservations",
        {"product_id": product_id, "quantity": quantity},
    )
    if status != HTTPStatus.CREATED:
        return status, reservation
    total = product["price"] * quantity
    try:
        with connect() as database:
            cursor = database.execute(
                "INSERT INTO orders "
                "(product_id, product_name, quantity, total, reservation_id, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (product_id, product["name"], quantity, total, reservation["id"], "confirmed"),
            )
            order_id = cursor.lastrowid
    except sqlite3.Error:
        post_json(
            "%s/reservations/%d/release" % (INVENTORY_URL, reservation["id"]),
            {},
        )
        raise
    return HTTPStatus.CREATED, {
        "id": order_id,
        "status": "confirmed",
        "product": product,
        "quantity": quantity,
        "total": total,
        "reservation": reservation,
    }


class Handler(JSONHandler, BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            catalog = get_json(CATALOG_URL + "/health")
            inventory = get_json(INVENTORY_URL + "/health")
            send_json(
                self,
                HTTPStatus.OK,
                {
                    "ok": catalog["ok"] and inventory["ok"],
                    "service": "shop-order-api",
                    "database": "sqlite",
                    "dependencies": ["shop-catalog-api", "shop-inventory-api"],
                },
            )
            return
        send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self):
        if self.path != "/checkout":
            send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            payload = read_json(self)
            status, order = create_order(
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
