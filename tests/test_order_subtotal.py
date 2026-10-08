"""Checks for integer-cent order subtotals."""

import importlib
import importlib.util
import unittest


class OrderSubtotalTests(unittest.TestCase):
    def operation(self):
        module_name = "smoke_demo.order_subtotal"
        self.assertIsNotNone(importlib.util.find_spec(module_name))
        return importlib.import_module(module_name).order_subtotal

    def test_positive_integer_inputs(self):
        self.assertEqual(self.operation()(199, 3), 597)

    def test_zero_quantity(self):
        self.assertEqual(self.operation()(199, 0), 0)

    def test_zero_price(self):
        self.assertEqual(self.operation()(0, 3), 0)
        self.assertEqual(self.operation()(0, 0), 0)

    def test_large_integers_remain_exact(self):
        self.assertEqual(self.operation()(10**30 + 1, 3), 3 * 10**30 + 3)

    def test_negative_price_rejected_even_for_zero_quantity(self):
        for quantity in (0, 3):
            with self.subTest(quantity=quantity):
                with self.assertRaisesRegex(ValueError, "unit_price_cents.*non-negative"):
                    self.operation()(-1, quantity)

    def test_negative_quantity_rejected(self):
        with self.assertRaisesRegex(ValueError, "quantity.*non-negative"):
            self.operation()(199, -1)

    def test_non_integer_price_rejected(self):
        for value in (1.0, 1.5, "199", None, True, False, [], float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(TypeError, "unit_price_cents.*integer"):
                    self.operation()(value, 0)

    def test_non_integer_quantity_rejected(self):
        for value in (1.0, 1.5, "3", None, True, False, [], float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(TypeError, "quantity.*integer"):
                    self.operation()(199, value)


if __name__ == "__main__":
    unittest.main()
