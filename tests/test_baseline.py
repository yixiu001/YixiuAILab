"""Minimal synthetic package import check."""

import importlib.util
import unittest


class BaselineTests(unittest.TestCase):
    def test_smoke_demo_package_exists(self):
        self.assertIsNotNone(importlib.util.find_spec("smoke_demo"))


if __name__ == "__main__":
    unittest.main()
