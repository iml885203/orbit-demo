from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import JSONHandler, port, send_json


PRODUCTS = [
    {
        "id": 1,
        "name": "Orbit Mug",
        "description": "A quiet reminder that every service is healthy.",
        "price": 18,
    },
    {
        "id": 2,
        "name": "Local Dev Hoodie",
        "description": "Host processes and containers, comfortably together.",
        "price": 52,
    },
]


class Handler(JSONHandler, BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            send_json(self, HTTPStatus.OK, {"ok": True, "service": "shop-catalog-api"})
            return
        if self.path == "/products":
            send_json(self, HTTPStatus.OK, {"products": PRODUCTS})
            return
        if self.path.startswith("/products/"):
            try:
                product_id = int(self.path.rsplit("/", 1)[1])
            except ValueError:
                send_json(self, HTTPStatus.BAD_REQUEST, {"error": "invalid product id"})
                return
            product = next((item for item in PRODUCTS if item["id"] == product_id), None)
            send_json(
                self,
                HTTPStatus.OK if product else HTTPStatus.NOT_FOUND,
                product or {"error": "product not found"},
            )
            return
        send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", port(28101)), Handler).serve_forever()
