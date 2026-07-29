"""Zero-package host service for Orbit's mixed-runtime quickstart."""

import html
import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "26379"))
HTTP_PORT = int(os.environ.get("PORT", os.environ.get("ORBIT_AUTO_PORT_DEMO_API", "28080")))


def redis_command(*parts):
    payload = ["*%d\r\n" % len(parts)]
    for part in parts:
        encoded = str(part).encode()
        payload.extend(("$%d\r\n" % len(encoded), encoded, b"\r\n"))

    with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=2) as connection:
        connection.sendall(b"".join(item.encode() if isinstance(item, str) else item for item in payload))
        response = connection.makefile("rb")
        prefix = response.read(1)
        value = response.readline().rstrip(b"\r\n").decode()

    if prefix == b":":
        return int(value)
    if prefix == b"+":
        return value
    if prefix == b"-":
        raise RuntimeError(value)
    raise RuntimeError("unexpected Redis response")


def page(visits):
    return """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Orbit is working</title>
<style>
  :root { color-scheme: dark; font-family: ui-sans-serif, system-ui, sans-serif; }
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #080b12; color: #eef2ff; }
  main { width: min(680px, calc(100%% - 40px)); }
  .eyebrow { color: #8ea3ff; letter-spacing: .14em; text-transform: uppercase; font-size: 12px; font-weight: 700; }
  h1 { margin: 14px 0 10px; font-size: clamp(36px, 7vw, 64px); line-height: 1; letter-spacing: -.04em; }
  .lead { color: #aab3c8; font-size: 18px; line-height: 1.6; margin-bottom: 30px; }
  .flow { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 14px; }
  .node { border: 1px solid #27304a; background: #111624; border-radius: 16px; padding: 20px; }
  .node strong { display: block; margin-bottom: 5px; }
  .node span, footer { color: #8d98b0; font-size: 14px; }
  .arrow { color: #6ee7b7; font-size: 24px; }
  .result { margin-top: 16px; padding: 20px; border-radius: 16px; background: #14251f; border: 1px solid #24634c; }
  .count { font-size: 34px; font-weight: 750; color: #6ee7b7; }
  footer { margin-top: 22px; line-height: 1.6; }
  code { color: #c7d2fe; }
  @media (max-width: 540px) { .flow { grid-template-columns: 1fr; } .arrow { transform: rotate(90deg); text-align: center; } }
</style>
<main>
  <div class="eyebrow">Orbit quickstart</div>
  <h1>Your mixed dev environment is live.</h1>
  <p class="lead">Orbit started a local Python process, waited for its Redis container, and injected the connection details.</p>
  <div class="flow">
    <div class="node"><strong>Python API</strong><span>running on your host</span></div>
    <div class="arrow">→</div>
    <div class="node"><strong>Redis 7.4</strong><span>running in Docker</span></div>
  </div>
  <div class="result"><div class="count">%d</div><div>visits stored in Redis — refresh to prove it</div></div>
  <footer>No package install was needed. Try <code>orbit status</code>, <code>orbit logs demo-api</code>, or <code>orbit open</code>.</footer>
</main>
</html>""" % visits


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/health":
                redis_command("PING")
                self.send_json(200, {"ok": True, "redis": "connected"})
                return
            if self.path == "/api/visits":
                self.send_json(200, {"visits": redis_command("INCR", "orbit:demo:visits")})
                return
            if self.path != "/":
                self.send_json(404, {"error": "not found"})
                return
            body = page(redis_command("INCR", "orbit:demo:visits")).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (OSError, RuntimeError, ValueError) as error:
            self.send_json(503, {"error": "Redis unavailable", "detail": html.escape(str(error))})

    def send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message, *args):
        print("%s - %s" % (self.address_string(), message % args), flush=True)


if __name__ == "__main__":
    print("demo-api listening on http://localhost:%d" % HTTP_PORT, flush=True)
    print("Redis connection injected by Orbit: %s:%d" % (REDIS_HOST, REDIS_PORT), flush=True)
    ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), Handler).serve_forever()
