#!/usr/bin/env python3
"""Local-only, stateless HTTP amount previews using the standard library."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import signal
import sys

from smoke_demo.format_cents import format_cents
from smoke_demo.order_subtotal import order_subtotal
from smoke_demo.shipping_fee import shipping_fee


MAX_BODY_BYTES = 65536
REQUEST_TIMEOUT_SECONDS = 5


def calculate_quote(payload):
    """Validate a decoded request and reuse the existing integer-cent helpers."""
    if not isinstance(payload, dict):
        raise ValueError("request must be a JSON object")
    for key in ("items", "shipping_fee_cents", "free_shipping_threshold_cents"):
        if key not in payload:
            raise ValueError(f"missing field: {key}")
    items = payload["items"]
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty array")
    subtotal = 0
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each item must be a JSON object")
        for key in ("unit_price_cents", "quantity"):
            if key not in item:
                raise ValueError(f"missing item field: {key}")
        subtotal += order_subtotal(item["unit_price_cents"], item["quantity"])
    shipping = shipping_fee(subtotal, payload["shipping_fee_cents"],
                            payload["free_shipping_threshold_cents"])
    total = subtotal + shipping
    return {"subtotal_cents": subtotal, "shipping_cents": shipping,
            "total_cents": total, "formatted_total": format_cents(total)}


def unique_object(pairs):
    """Do not let duplicate JSON keys silently replace monetary inputs."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def parse_integer(value):
    """Decode integer chunks without altering Python's global digit limit."""
    negative = value.startswith("-")
    digits = value[1:] if negative else value
    result = 0
    for start in range(0, len(digits), 9):
        chunk = digits[start:start + 9]
        result = result * (10 ** len(chunk)) + int(chunk)
    return -result if negative else result


def reject_constant(value):
    raise ValueError("non-standard JSON number")


def encode_response(payload):
    """Encode our flat response objects, including exact very large integers."""
    parts = []
    for key, value in payload.items():
        if type(value) is int:
            encoded = format_cents(value).replace(".", "").lstrip("0") or "0"
        else:
            encoded = json.dumps(value)
        parts.append(json.dumps(key) + ":" + encoded)
    return ("{" + ",".join(parts) + "}").encode("utf-8")


class QuoteHandler(BaseHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(REQUEST_TIMEOUT_SECONDS)
        super().setup()

    def log_message(self, format, *args):
        """Do not retain request URLs, bodies, or client addresses in logs."""

    def respond(self, status, payload):
        body = encode_response(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except OSError:
                pass  # A disconnected client must not interrupt the service.

    def send_error(self, code, message=None, explain=None):
        # Keep malformed HTTP errors JSON and avoid reflecting request data.
        self.respond(code, {"error": "invalid HTTP request"})

    def route(self):
        if self.path not in ("/health", "/quote"):
            self.respond(404, {"error": "not found"})
        elif self.path == "/health" and self.command == "GET":
            self.respond(200, {"status": "ok"})
        elif self.path == "/quote" and self.command == "POST":
            self.quote()
        else:
            self.respond(405, {"error": "method not allowed"})

    do_GET = route
    do_POST = route
    do_PUT = route
    do_DELETE = route
    do_PATCH = route
    do_HEAD = route
    do_OPTIONS = route

    def quote(self):
        try:
            lengths = self.headers.get_all("Content-Length", [])
            if self.headers.get("Transfer-Encoding") or len(lengths) != 1:
                raise ValueError("one Content-Length header is required; chunked bodies are not supported")
            if not lengths[0].isascii() or not lengths[0].isdigit():
                raise ValueError("invalid Content-Length")
            length = int(lengths[0])
            if not 0 < length <= MAX_BODY_BYTES:
                raise ValueError("body must contain 1 to 65536 bytes")
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError("incomplete request body")
            payload = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                                 parse_int=parse_integer, parse_constant=reject_constant)
            result = calculate_quote(payload)
        except (ValueError, TypeError, RecursionError):
            self.respond(400, {"error": "invalid quote request: use all required fields and non-negative integers"})
            return
        except OSError:
            self.respond(400, {"error": "incomplete or timed out request body"})
            return
        self.respond(200, result)


def port_number(value):
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("port must be an integer from 0 to 65535") from None
    if not 0 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be an integer from 0 to 65535")
    return port


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=port_number, default=8001,
                        help="loopback port (default: 8001; 0 chooses a free port)")
    args = parser.parse_args(argv)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), QuoteHandler)
    except OSError as error:
        print(f"could not listen on 127.0.0.1:{args.port}: {error.strerror}", file=sys.stderr)
        return 1

    def stop(signum, frame):
        raise KeyboardInterrupt

    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        with server:
            print(f"http://127.0.0.1:{server.server_port}", flush=True)
            server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
