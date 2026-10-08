"""Synthetic division checks."""

import importlib
import importlib.util
import unittest


class DivisionTests(unittest.TestCase):
    def setUp(self):
        module_name = "smoke_demo.division"
        self.assertIsNotNone(importlib.util.find_spec(module_name))
        self.divide = importlib.import_module(module_name).divide

    def test_positive_numbers_use_true_division(self):
        for a, b in [(6, 3), (7, 2), (7.5, 2.5), (1, 3)]:
            with self.subTest(a=a, b=b):
                result = self.divide(a, b)
                self.assertEqual(result, a / b)
                self.assertIsInstance(result, float)

    def test_negative_numbers(self):
        for a, b in [(-7, 2), (7, -2), (-7, -2), (-7.5, 2.5)]:
            with self.subTest(a=a, b=b):
                self.assertEqual(self.divide(a, b), a / b)

    def test_zero_dividend(self):
        for a, b in [(0, 3), (0, -3), (0.0, 2.5)]:
            with self.subTest(a=a, b=b):
                self.assertEqual(self.divide(a, b), a / b)

    def test_zero_divisor_raises_value_error(self):
        for a in (5, -5, 0):
            for b in (0, 0.0, -0.0):
                with self.subTest(a=a, b=b):
                    with self.assertRaises(ValueError):
                        self.divide(a, b)


if __name__ == "__main__":
    unittest.main()
