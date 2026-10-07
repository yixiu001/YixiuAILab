"""Synthetic integer subtraction checks."""

import importlib
import importlib.util
import unittest


class SubtractionTests(unittest.TestCase):
    def test_integer_subtraction(self):
        module_name = "smoke_demo.subtraction"
        self.assertIsNotNone(importlib.util.find_spec(module_name))
        operation = importlib.import_module(module_name).subtract
        cases = [(7, 3, 4), (3, 7, -4), (-3, -2, -1), (7, 0, 7)]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(operation(left, right), expected)


if __name__ == "__main__":
    unittest.main()
