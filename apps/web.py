import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from common import JSONHandler, port, send_json


CATALOG_URL = os.environ.get("SHOP_CATALOG_API_URL", "http://127.0.0.1:28101")
INVENTORY_URL = os.environ.get("SHOP_INVENTORY_API_URL", "http://127.0.0.1:28102")
ORDER_URL = os.environ.get("SHOP_ORDER_API_URL", "http://127.0.0.1:28103")


class Handler(JSONHandler, BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            send_json(self, HTTPStatus.OK, {"ok": True, "service": "demo-shop"})
            return
        if self.path not in ("/", "/index.html"):
            send_json(self, HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        template = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
        body = (
            template.replace("{{CATALOG_URL}}", CATALOG_URL)
            .replace("{{INVENTORY_URL}}", INVENTORY_URL)
            .replace("{{ORDER_URL}}", ORDER_URL)
            .encode()
        )
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", port(28080)), Handler).serve_forever()
