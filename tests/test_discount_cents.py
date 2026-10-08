"""Checks for exact integer-cent discount deductions."""

import importlib
import importlib.util
import unittest


class DiscountCentsTests(unittest.TestCase):
    def operation(self):
        module_name = "smoke_demo.discount_cents"
        self.assertIsNotNone(importlib.util.find_spec(module_name))
        return importlib.import_module(module_name).discount_cents

    def test_discount_below_amount(self):
        self.assertEqual(self.operation()(1999, 500), 1499)

    def test_discount_equal_to_amount(self):
        self.assertEqual(self.operation()(500, 500), 0)

    def test_discount_above_amount(self):
        self.assertEqual(self.operation()(500, 501), 0)

    def test_zero_discount(self):
        self.assertEqual(self.operation()(1999, 0), 1999)

    def test_zero_amount(self):
        self.assertEqual(self.operation()(0, 500), 0)
        self.assertEqual(self.operation()(0, 0), 0)

    def test_large_integers_remain_exact(self):
        operation = self.operation()
        self.assertEqual(operation(9007199254740993, 2), 9007199254740991)
        amount = 10**5000 + 7
        self.assertEqual(operation(amount, 3), 10**5000 + 4)
        self.assertEqual(operation(amount, amount - 1), 1)
        self.assertEqual(operation(amount, amount), 0)
        self.assertEqual(operation(amount, amount + 1), 0)

    def test_negative_inputs_rejected(self):
        operation = self.operation()
        for index, name in enumerate(("amount_cents", "discount_cents")):
            for valid_inputs in ((1999, 500), (500, 501), (0, 0)):
                arguments = list(valid_inputs)
                arguments[index] = -1
                with self.subTest(name=name, arguments=arguments):
                    with self.assertRaisesRegex(ValueError, f"{name}.*non-negative"):
                        operation(*arguments)

    def test_boolean_inputs_rejected(self):
        operation = self.operation()
        for index, name in enumerate(("amount_cents", "discount_cents")):
            for value in (True, False):
                arguments = [0, 0]
                arguments[index] = value
                with self.subTest(name=name, value=value):
                    with self.assertRaisesRegex(TypeError, f"{name}.*integer"):
                        operation(*arguments)

    def test_non_integer_inputs_rejected(self):
        operation = self.operation()
        invalid_values = (1.0, 1.5, "500", None, [], {}, float("nan"), float("inf"))
        for index, name in enumerate(("amount_cents", "discount_cents")):
            for valid_inputs in ((1999, 500), (500, 501), (0, 0)):
                for value in invalid_values:
                    arguments = list(valid_inputs)
                    arguments[index] = value
                    with self.subTest(name=name, arguments=arguments):
                        with self.assertRaisesRegex(TypeError, f"{name}.*integer"):
                            operation(*arguments)


if __name__ == "__main__":
    unittest.main()
