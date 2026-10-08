#!/usr/bin/env python3
"""Preview a local UTF-8 CSV quote without starting or contacting a server."""

import argparse
import csv
import sys

from quote_server import calculate_quote, encode_response, parse_integer


FIELDS = ("unit_price_cents", "quantity")


def non_negative_integer(value):
    """Accept ASCII decimal digits, allowing surrounding whitespace."""
    digits = value.strip()
    if not digits or not digits.isascii() or not digits.isdigit():
        raise ValueError("must be a non-negative integer")
    return parse_integer(digits)


def read_items(path):
    """Read rows without writing, logging, or uploading the input file."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, strict=True)
            header = next((row for row in reader if row), None)
            if header is None:
                raise ValueError("CSV contains no items")
            if len(set(header)) != len(header):
                raise ValueError("duplicate CSV column")
            for field in FIELDS:
                if field not in header:
                    raise ValueError(f"missing CSV column: {field}")
            columns = {field: header.index(field) for field in FIELDS}
            items = []
            for row in reader:
                if not row:
                    continue
                if len(row) != len(header):
                    raise ValueError(f"row {reader.line_num}: wrong number of columns")
                item = {}
                for field, column in columns.items():
                    try:
                        item[field] = non_negative_integer(row[column])
                    except ValueError:
                        raise ValueError(
                            f"row {reader.line_num}: {field} must be a non-negative integer"
                        ) from None
                items.append(item)
            if not items:
                raise ValueError("CSV contains no items")
            return items
    except UnicodeError:
        raise ValueError("CSV must be UTF-8") from None
    except csv.Error:
        raise ValueError("invalid CSV") from None
    except OSError:
        raise ValueError("cannot read CSV file") from None


class QuoteArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, f"{self.prog}: error: {message}\n")


def amount_argument(value):
    try:
        return non_negative_integer(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def main(argv=None):
    parser = QuoteArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="local UTF-8 CSV path (BOM is accepted)")
    parser.add_argument("--shipping-fee-cents", required=True, type=amount_argument,
                        help="base shipping fee in non-negative integer cents")
    parser.add_argument("--free-shipping-threshold-cents", required=True,
                        type=amount_argument, help="free-shipping threshold in integer cents")
    args = parser.parse_args(argv)
    try:
        quote = calculate_quote({
            "items": read_items(args.csv_path),
            "shipping_fee_cents": args.shipping_fee_cents,
            "free_shipping_threshold_cents": args.free_shipping_threshold_cents,
        })
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(encode_response(quote).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
