"""Real HTTP and subprocess tests; every listener uses an OS-assigned port."""

import copy
import http.client
import json
import os
from pathlib import Path
import queue
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "quote_server.py"
VALID = {
    "items": [{"unit_price_cents": 199, "quantity": 3},
              {"unit_price_cents": 250, "quantity": 2}],
    "shipping_fee_cents": 500,
    "free_shipping_threshold_cents": 5000,
}


def stop_process(process):
    """Only signal a child we created, and bound every wait."""
    if process.poll() is None:
        process.terminate()
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate(timeout=5)


def start_service(test_case, cwd=ROOT):
    process = subprocess.Popen(
        [sys.executable, "-B", str(SCRIPT), "--port", "0"],
        cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    test_case.addCleanup(stop_process, process)
    lines = queue.Queue()
    reader = threading.Thread(target=lambda: lines.put(process.stdout.readline()),
                              daemon=True)
    reader.start()
    line = lines.get(timeout=5).strip()
    test_case.assertRegex(line, r"^http://127\.0\.0\.1:[0-9]+$",
                         "Service must print its actual loopback URL")
    port = urlsplit(line).port
    test_case.assertNotEqual(port, 8000)
    return process, port


class QuoteHTTPTests(unittest.TestCase):
    def setUp(self):
        self.process, self.port = start_service(self)

    def request(self, method="POST", path="/quote", payload=VALID, raw=None,
                headers=None):
        body = json.dumps(payload).encode("utf-8") if raw is None else raw
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        self.addCleanup(connection.close)
        connection.request(method, path, body=body,
                           headers=headers or {"Content-Type": "application/json"})
        response = connection.getresponse()
        data = response.read()
        self.assertEqual(response.getheader("Content-Type"), "application/json; charset=utf-8")
        self.assertEqual(int(response.getheader("Content-Length")), len(data))
        self.assertEqual(response.getheader("Cache-Control"), "no-store")
        return response.status, json.loads(data)

    def assert_bad(self, payload=VALID, raw=None, headers=None):
        status, response = self.request(payload=payload, raw=raw, headers=headers)
        self.assertEqual(status, 400)
        self.assertEqual(list(response), ["error"])
        self.assertIsInstance(response["error"], str)
        self.assertTrue(response["error"])

    def test_health(self):
        self.assertEqual(self.request("GET", "/health"), (200, {"status": "ok"}))

    def test_standard_shipping(self):
        self.assertEqual(self.request(), (200, {
            "subtotal_cents": 1097, "shipping_cents": 500,
            "total_cents": 1597, "formatted_total": "15.97",
        }))

    def test_free_shipping_at_and_above_threshold(self):
        for subtotal in (5000, 5001):
            with self.subTest(subtotal=subtotal):
                payload = copy.deepcopy(VALID)
                payload["items"] = [{"unit_price_cents": subtotal, "quantity": 1}]
                status, result = self.request(payload=payload)
                self.assertEqual(status, 200)
                self.assertEqual(result["shipping_cents"], 0)
                self.assertEqual(result["total_cents"], subtotal)

    def test_zero_quantity_price_and_threshold(self):
        payload = {"items": [{"unit_price_cents": 99, "quantity": 0},
                             {"unit_price_cents": 0, "quantity": 5}],
                   "shipping_fee_cents": 500, "free_shipping_threshold_cents": 0}
        self.assertEqual(self.request(payload=payload), (200, {
            "subtotal_cents": 0, "shipping_cents": 0,
            "total_cents": 0, "formatted_total": "0.00",
        }))

    def test_large_integer_amount_stays_exact(self):
        payload = copy.deepcopy(VALID)
        payload["items"] = [{"unit_price_cents": 9007199254740993, "quantity": 3}]
        status, result = self.request(payload=payload)
        self.assertEqual(status, 200)
        self.assertEqual(result["total_cents"], 27021597764222979)
        self.assertEqual(result["formatted_total"], "270215977642229.79")

    def test_each_amount_and_quantity_rejects_non_integer_or_negative(self):
        for key in ("unit_price_cents", "quantity", "shipping_fee_cents",
                    "free_shipping_threshold_cents"):
            for value in (-1, True, False, 1.0, "1", None, [], {}):
                with self.subTest(key=key, value=value):
                    payload = copy.deepcopy(VALID)
                    target = payload["items"][0] if key in ("unit_price_cents", "quantity") else payload
                    target[key] = value
                    self.assert_bad(payload)

    def test_all_fields_required(self):
        for key in VALID:
            with self.subTest(key=key):
                payload = copy.deepcopy(VALID)
                del payload[key]
                self.assert_bad(payload)
        for key in VALID["items"][0]:
            with self.subTest(key=key):
                payload = copy.deepcopy(VALID)
                del payload["items"][0][key]
                self.assert_bad(payload)

    def test_request_and_items_shape(self):
        for payload in (None, [], 0, "quote", True):
            with self.subTest(payload=payload):
                self.assert_bad(payload)
        for items in ([], {}, "items", None, [None], [1], [[]]):
            with self.subTest(items=items):
                payload = copy.deepcopy(VALID)
                payload["items"] = items
                self.assert_bad(payload)

    def test_invalid_price_with_zero_quantity_is_rejected(self):
        payload = copy.deepcopy(VALID)
        payload["items"] = [{"unit_price_cents": -1, "quantity": 0}]
        self.assert_bad(payload)

    def test_invalid_shipping_is_rejected_when_shipping_would_be_free(self):
        payload = copy.deepcopy(VALID)
        payload["free_shipping_threshold_cents"] = 0
        payload["shipping_fee_cents"] = True
        self.assert_bad(payload)

    def test_bad_json_and_invalid_utf8(self):
        for raw in (b"", b"{", b"{} trailing", b"\xff", b'{"items":NaN}'):
            with self.subTest(raw=raw):
                self.assert_bad(raw=raw)

    def test_duplicate_json_keys_are_rejected(self):
        self.assert_bad(raw=b'{"items":[],"items":[{"unit_price_cents":1,"quantity":1}],"shipping_fee_cents":0,"free_shipping_threshold_cents":0}')

    def test_body_limit_and_invalid_content_length(self):
        self.assert_bad(raw=b" " * 65537)
        for length in ("-1", "invalid"):
            with self.subTest(length=length):
                self.assert_bad(raw=b"", headers={"Content-Length": length})

    def test_unknown_paths_are_404(self):
        for method in ("GET", "POST", "PUT", "DELETE", "TRACE", "CUSTOM"):
            with self.subTest(method=method):
                status, result = self.request(method, "/unknown")
                self.assertEqual(status, 404)
                self.assertEqual(result, {"error": "not found"})

    def test_unsupported_methods_on_known_paths_are_405(self):
        for method, path in (("GET", "/quote"), ("POST", "/health"),
                             ("TRACE", "/quote"), ("CUSTOM", "/health")):
            with self.subTest(method=method, path=path):
                self.assertEqual(self.request(method, path),
                                 (405, {"error": "method not allowed"}))

    def test_paths_match_exactly(self):
        for path in ("//health", "/health/", "/health?query=1"):
            with self.subTest(path=path):
                self.assertEqual(self.request("GET", path)[0], 404)

    @unittest.skipUnless(os.name == "posix", "RST uses POSIX SO_LINGER layout")
    def test_reset_clients_do_not_log_client_data(self):
        for request in (b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n",
                        b"GET /health HTTP/1.1\r\nHost: "):
            for _ in range(10):
                with socket.create_connection(("127.0.0.1", self.port), timeout=3) as client:
                    client.sendall(request)
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                self.assertEqual(self.request("GET", "/health")[0], 200)
        self.process.terminate()
        stdout, stderr = self.process.communicate(timeout=5)
        self.assertEqual(self.process.returncode, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_bad_request_does_not_stop_next_request(self):
        self.assert_bad(raw=b"{")
        self.assertEqual(self.request()[0], 200)

    def test_slow_connection_does_not_block_health(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=3) as slow:
            slow.sendall(b"POST /quote HTTP/1.1\r\nHost: localhost\r\nContent-Length: 99\r\n\r\n{")
            self.assertEqual(self.request("GET", "/health")[0], 200)


class QuoteCLITests(unittest.TestCase):
    def test_can_start_from_another_directory_and_exit_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            process, port = start_service(self, cwd=directory)
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0)
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")
            with self.assertRaises(OSError):
                socket.create_connection(("127.0.0.1", port), timeout=1)
            self.assertEqual(list(Path(directory).iterdir()), [])

    @unittest.skipUnless(os.name == "posix", "SIGINT test requires POSIX")
    def test_interrupt_exits_cleanly(self):
        process, _ = start_service(self)
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(stderr, "")

    def test_occupied_port_preserves_other_listener(self):
        with socket.socket() as existing:
            existing.bind(("127.0.0.1", 0))
            existing.listen()
            port = existing.getsockname()[1]
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--port", str(port)],
                capture_output=True, text=True, timeout=5,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("could not listen", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                pass

    def test_invalid_ports_and_non_loopback_option_are_rejected(self):
        for args in (["--port", "-1"], ["--port", "65536"],
                     ["--port", "bad"], ["--host", "0.0.0.0"]):
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, "-B", str(SCRIPT), *args],
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stderr)

    def test_import_has_no_output_or_listener(self):
        result = subprocess.run([sys.executable, "-B", "-c", "import quote_server"],
                                cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
