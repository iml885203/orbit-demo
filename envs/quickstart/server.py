import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def redis_status():
    host = os.environ.get("REDIS_HOST", "localhost")
    port = int(os.environ.get("REDIS_PORT", "26379"))
    try:
        with socket.create_connection((host, port), timeout=1):
            return {"connected": True, "host": host, "port": port}
    except OSError as error:
        return {
            "connected": False,
            "host": host,
            "port": port,
            "error": str(error),
        }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = {
            "service": "demo-api",
            "message": "Orbit is coordinating a host service and a container.",
            "redis": redis_status(),
        }
        status = 200
        if self.path == "/health" and not payload["redis"]["connected"]:
            status = 503
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message, *args):
        print("%s - %s" % (self.address_string(), message % args), flush=True)


def main():
    port = int(os.environ.get("PORT", "28080"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("demo-api listening on http://localhost:%d" % port, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
