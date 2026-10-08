"""Checks for integer-cent shipping fees and free-shipping thresholds."""

import importlib
import importlib.util
import unittest


class ShippingFeeTests(unittest.TestCase):
    def operation(self):
        module_name = "smoke_demo.shipping_fee"
        self.assertIsNotNone(importlib.util.find_spec(module_name))
        return importlib.import_module(module_name).shipping_fee

    def test_subtotal_below_threshold(self):
        self.assertEqual(self.operation()(4999, 500, 5000), 500)

    def test_subtotal_at_threshold(self):
        self.assertEqual(self.operation()(5000, 500, 5000), 0)

    def test_subtotal_above_threshold(self):
        self.assertEqual(self.operation()(5001, 500, 5000), 0)

    def test_zero_subtotal(self):
        self.assertEqual(self.operation()(0, 500, 5000), 500)

    def test_zero_base_fee(self):
        self.assertEqual(self.operation()(4999, 0, 5000), 0)

    def test_zero_threshold(self):
        self.assertEqual(self.operation()(0, 500, 0), 0)
        self.assertEqual(self.operation()(5000, 500, 0), 0)
        self.assertEqual(self.operation()(0, 0, 0), 0)

    def test_large_integers_remain_exact(self):
        threshold = 10**30 + 1
        base_fee = 10**30 + 7
        self.assertEqual(self.operation()(threshold - 1, base_fee, threshold), base_fee)
        self.assertEqual(self.operation()(threshold, base_fee, threshold), 0)
        self.assertEqual(self.operation()(threshold + 1, base_fee, threshold), 0)

    def test_negative_inputs_rejected(self):
        names = ("cart_subtotal_cents", "base_fee_cents", "free_shipping_threshold_cents")
        for index, name in enumerate(names):
            for valid_inputs in ((0, 500, 5000), (5000, 500, 5000), (0, 0, 0)):
                arguments = list(valid_inputs)
                arguments[index] = -1
                with self.subTest(name=name, arguments=arguments):
                    with self.assertRaisesRegex(ValueError, f"{name}.*non-negative"):
                        self.operation()(*arguments)

    def test_non_integer_inputs_rejected(self):
        names = ("cart_subtotal_cents", "base_fee_cents", "free_shipping_threshold_cents")
        invalid_values = (1.0, 1.5, "500", None, True, False, [], float("nan"), float("inf"))
        for index, name in enumerate(names):
            for valid_inputs in ((0, 500, 5000), (5000, 500, 5000), (0, 0, 0)):
                for value in invalid_values:
                    arguments = list(valid_inputs)
                    arguments[index] = value
                    with self.subTest(name=name, arguments=arguments):
                        with self.assertRaisesRegex(TypeError, f"{name}.*integer"):
                            self.operation()(*arguments)


if __name__ == "__main__":
    unittest.main()
