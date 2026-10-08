"""Checks for exact integer-cent formatting as yuan strings."""

import importlib
import importlib.util
import unittest


class FormatCentsTests(unittest.TestCase):
    def operation(self):
        module_name = "smoke_demo.format_cents"
        self.assertIsNotNone(importlib.util.find_spec(module_name))
        return importlib.import_module(module_name).format_cents

    def test_zero(self):
        self.assertEqual(self.operation()(0), "0.00")

    def test_sub_yuan_amounts(self):
        for amount_cents, expected in ((1, "0.01"), (9, "0.09"), (10, "0.10"), (99, "0.99")):
            with self.subTest(amount_cents=amount_cents):
                self.assertEqual(self.operation()(amount_cents), expected)

    def test_whole_yuan_amounts(self):
        for amount_cents, expected in ((100, "1.00"), (1000, "10.00")):
            with self.subTest(amount_cents=amount_cents):
                self.assertEqual(self.operation()(amount_cents), expected)

    def test_mixed_yuan_and_cent_amounts(self):
        for amount_cents, expected in ((101, "1.01"), (110, "1.10"), (199, "1.99"), (12345, "123.45")):
            with self.subTest(amount_cents=amount_cents):
                self.assertEqual(self.operation()(amount_cents), expected)

    def test_large_integers_remain_exact(self):
        self.assertEqual(self.operation()(9007199254740993), "90071992547409.93")
        self.assertEqual(self.operation()(10**400 + 7), "1" + "0" * 398 + ".07")

    def test_decimal_chunk_boundaries(self):
        self.assertEqual(self.operation()(99999999999), "999999999.99")
        self.assertEqual(self.operation()(100000000000), "1000000000.00")
        self.assertEqual(self.operation()(100000000001), "1000000000.01")

    def test_integers_beyond_default_string_conversion_limit(self):
        self.assertEqual(self.operation()(10**5000 + 7), "1" + "0" * 4998 + ".07")
        self.assertEqual(self.operation()(10**5000 - 1), "9" * 4998 + ".99")

    def test_negative_integers_rejected(self):
        for amount_cents in (-1, -100, -(10**400)):
            with self.subTest(amount_cents=amount_cents):
                with self.assertRaisesRegex(ValueError, "amount_cents.*non-negative"):
                    self.operation()(amount_cents)

    def test_non_integer_inputs_rejected(self):
        invalid_values = (True, False, 0.0, 1.5, -1.0, "100", None, [], {}, float("nan"), float("inf"))
        for amount_cents in invalid_values:
            with self.subTest(amount_cents=amount_cents):
                with self.assertRaisesRegex(TypeError, "amount_cents.*integer"):
                    self.operation()(amount_cents)


if __name__ == "__main__":
    unittest.main()
