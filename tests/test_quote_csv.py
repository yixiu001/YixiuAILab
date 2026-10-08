"""Local CSV quotes use synthetic files and never need a running HTTP server."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from quote_server import calculate_quote, encode_response, parse_integer


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "quote_csv.py"
HEADER = "unit_price_cents,quantity\n"
DEFAULT_FLAGS = ["--shipping-fee-cents", "500",
                 "--free-shipping-threshold-cents", "5000"]


class QuoteCSVTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.csv = self.directory / "合成 报价.csv"

    def run_cli(self, content=HEADER + "199,3\n250,2\n", flags=None, path=None):
        self.assertTrue(SCRIPT.is_file(), "The local CSV entry point must exist")
        if content is not None:
            if isinstance(content, bytes):
                self.csv.write_bytes(content)
            else:
                self.csv.write_text(content, encoding="utf-8", newline="")
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(path or self.csv),
             *(DEFAULT_FLAGS if flags is None else flags)],
            cwd=self.directory, capture_output=True, text=True, timeout=5,
        )

    def assert_error(self, result, text):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn(text, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertLess(len(result.stderr), 500)

    def test_output_matches_existing_quote_json_exactly(self):
        result = self.run_cli()
        expected = calculate_quote({
            "items": [{"unit_price_cents": 199, "quantity": 3},
                      {"unit_price_cents": 250, "quantity": 2}],
            "shipping_fee_cents": 500, "free_shipping_threshold_cents": 5000,
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, encode_response(expected).decode() + "\n")
        self.assertEqual(result.stderr, "")

    def test_shipping_threshold_zero_and_large_amounts(self):
        cases = ((4999, 1, 5000, 500, 5499), (5000, 1, 5000, 0, 5000),
                 (5001, 1, 5000, 0, 5001), (199, 0, 5000, 500, 500),
                 (0, 5, 0, 0, 0), (9007199254740993, 3, 5000, 0, 27021597764222979))
        for price, quantity, threshold, shipping, total in cases:
            with self.subTest(price=price, quantity=quantity, threshold=threshold):
                result = self.run_cli(HEADER + f"{price},{quantity}\n", flags=[
                    "--shipping-fee-cents", "500",
                    "--free-shipping-threshold-cents", str(threshold)])
                self.assertEqual(result.returncode, 0, result.stderr)
                quote = json.loads(result.stdout)
                self.assertEqual(quote["shipping_cents"], shipping)
                self.assertEqual(quote["total_cents"], total)

    def test_huge_integers_use_existing_exact_encoding(self):
        digits = "1" + "0" * 5000
        result = self.run_cli(HEADER + digits + ",1\n", flags=[
            "--shipping-fee-cents", "0", "--free-shipping-threshold-cents", digits])
        self.assertEqual(result.returncode, 0, result.stderr)
        quote = json.loads(result.stdout, parse_int=parse_integer)
        self.assertEqual(quote["total_cents"], 10**5000)
        self.assertEqual(quote["formatted_total"], "1" + "0" * 4998 + ".00")

    def test_bom_crlf_quoted_fields_blank_lines_and_reordered_columns(self):
        content = '\ufeffquantity,note,unit_price_cents\r\n\r\n"3","synthetic, only"," 0199 "\r\n'
        result = self.run_cli(content)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["subtotal_cents"], 597)

    def test_empty_file_header_only_and_blank_only_are_errors(self):
        for content in ("", "\n\n", HEADER, HEADER + "\n\n", "\ufeff"):
            with self.subTest(content=content):
                self.assert_error(self.run_cli(content), "CSV contains no items")

    def test_missing_columns(self):
        for content, field in (("quantity\n2\n", "unit_price_cents"),
                               ("unit_price_cents\n199\n", "quantity")):
            with self.subTest(field=field):
                self.assert_error(self.run_cli(content), "missing CSV column: " + field)

    def test_duplicate_columns_are_errors(self):
        self.assert_error(self.run_cli("unit_price_cents,quantity,quantity\n199,1,2\n"),
                          "duplicate CSV column")

    def test_invalid_integer_cells_identify_row_and_field(self):
        for value in ("", "-1", "1.0", "1e2", "NaN", "true", "1_000", "+1", "１２", "bad"):
            for index, field in enumerate(("unit_price_cents", "quantity")):
                with self.subTest(value=value, field=field):
                    row = ["199", "0"]
                    row[index] = value
                    self.assert_error(self.run_cli(HEADER + ",".join(row) + "\n"),
                                      f"row 2: {field} must be a non-negative integer")

    def test_missing_or_extra_cells_are_errors(self):
        for row in ("199\n", "199,2,3\n"):
            with self.subTest(row=row):
                self.assert_error(self.run_cli(HEADER + row), "row 2: wrong number of columns")

    def test_malformed_csv_is_short_error(self):
        self.assert_error(self.run_cli(HEADER + '"199,2\n'), "invalid CSV")

    def test_invalid_encoding_is_short_error(self):
        self.assert_error(self.run_cli(b"unit_price_cents,quantity\n\xff,1\n"),
                          "CSV must be UTF-8")

    def test_missing_and_directory_paths_are_short_errors(self):
        for path in (self.directory / "不存在.csv", self.directory):
            with self.subTest(path=path):
                self.assert_error(self.run_cli(content=None, path=path), "cannot read CSV file")

    def test_shipping_options_are_required_and_validated_even_when_free(self):
        for flags in ([], ["--shipping-fee-cents", "500"],
                      ["--free-shipping-threshold-cents", "5000"]):
            self.assert_error(self.run_cli(flags=flags), "required")
        for option in ("--shipping-fee-cents", "--free-shipping-threshold-cents"):
            for value in ("-1", "1.0", "bad", "1_000", "true"):
                with self.subTest(option=option, value=value):
                    flags = ["--shipping-fee-cents", "0",
                             "--free-shipping-threshold-cents", "0"]
                    flags[flags.index(option) + 1] = value
                    self.assert_error(self.run_cli(flags=flags),
                                      "must be a non-negative integer")

    def test_input_unchanged_and_no_output_files(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.csv.read_text(), HEADER + "199,3\n250,2\n")
        self.assertEqual(list(self.directory.iterdir()), [self.csv])

    def test_import_has_no_output(self):
        self.assertTrue(SCRIPT.is_file(), "The local CSV entry point must exist")
        result = subprocess.run([sys.executable, "-B", "-c", "import quote_csv"],
                                cwd=ROOT, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_cli_does_not_open_network_sockets(self):
        self.assertTrue(SCRIPT.is_file(), "The local CSV entry point must exist")
        self.csv.write_text(HEADER + "199,3\n", encoding="utf-8")
        probe = '''import runpy, sys
sys.path.insert(0, sys.argv[1])
def forbid_network(event, args):
    if event.startswith("socket."):
        raise AssertionError("CSV quote must not use the network")
sys.addaudithook(forbid_network)
sys.argv = sys.argv[2:]
runpy.run_path(sys.argv[0], run_name="__main__")
'''
        result = subprocess.run([sys.executable, "-B", "-c", probe, str(ROOT),
                                 str(SCRIPT), str(self.csv), *DEFAULT_FLAGS],
                                cwd=self.directory, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["total_cents"], 1097)


if __name__ == "__main__":
    unittest.main()
