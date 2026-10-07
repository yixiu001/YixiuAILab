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


if __name__ == "__main__":
    unittest.main()
