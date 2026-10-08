"""Synthetic integer addition checks."""

import importlib
import importlib.util
import unittest


class AdditionTests(unittest.TestCase):
    def test_integer_addition(self):
        module_name = "smoke_demo.addition"
        self.assertIsNotNone(importlib.util.find_spec(module_name))
        operation = importlib.import_module(module_name).add
        cases = [(2, 3, 5), (-3, -2, -5), (7, 0, 7), (-2, 5, 3)]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(operation(left, right), expected)


class AddCentsTests(unittest.TestCase):
    def operation(self):
        module = importlib.import_module("smoke_demo.addition")
        operation = getattr(module, "add_cents", None)
        self.assertTrue(callable(operation), "add_cents must be available")
        return operation

    def test_positive_integer_cents(self):
        self.assertEqual(self.operation()(199, 250), 449)

    def test_zero_cents(self):
        for left, right, expected in ((0, 0, 0), (0, 199, 199), (199, 0, 199)):
            with self.subTest(left=left, right=right):
                self.assertEqual(self.operation()(left, right), expected)

    def test_large_integer_cents_remain_exact(self):
        self.assertEqual(self.operation()(10**30 + 1, 10**30 + 2), 2 * 10**30 + 3)

    def test_negative_cents_rejected(self):
        operation = self.operation()
        for left, right in ((-1, 0), (0, -1), (-1, -1)):
            with self.subTest(left=left, right=right):
                with self.assertRaises(ValueError):
                    operation(left, right)

    def test_boolean_cents_rejected_in_either_operand(self):
        operation = self.operation()
        for value in (True, False):
            for left, right in ((value, 0), (0, value)):
                with self.subTest(left=left, right=right):
                    with self.assertRaises(TypeError):
                        operation(left, right)

    def test_non_integer_cents_rejected_in_either_operand(self):
        operation = self.operation()
        for value in (1.0, 1.5, "199", None, [], float("nan"), float("inf")):
            for left, right in ((value, 0), (0, value)):
                with self.subTest(left=left, right=right):
                    with self.assertRaises(TypeError):
                        operation(left, right)


if __name__ == "__main__":
    unittest.main()
