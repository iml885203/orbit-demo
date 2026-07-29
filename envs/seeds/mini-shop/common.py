import json
import os
from http import HTTPStatus
from pathlib import Path
from urllib import error, request


def data_path(name):
    orbit_home = Path(os.environ.get("ORBIT_HOME", Path.home() / ".orbit"))
    directory = orbit_home / "demo-data" / "mini-shop"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / name


def port(default):
    return int(os.environ.get("PORT", default))


def read_json(handler):
    size = int(handler.headers.get("Content-Length", "0"))
    return json.loads(handler.rfile.read(size) or b"{}")


def send_json(handler, status, payload):
    body = json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def get_json(url):
    with request.urlopen(url, timeout=2) as response:
        return json.load(response)


def post_json(url, payload):
    body = json.dumps(payload).encode()
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=3) as response:
            return response.status, json.load(response)
    except error.HTTPError as response:
        return response.code, json.load(response)


class JSONHandler:
    def do_OPTIONS(self):
        send_json(self, HTTPStatus.NO_CONTENT, {})

    def log_message(self, message, *args):
        print("%s - %s" % (self.address_string(), message % args), flush=True)
