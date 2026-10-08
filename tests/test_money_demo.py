"""End-to-end checks for the directly runnable amount example."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "money_demo.py"
EXPECTED_OUTPUT = (
    "Standard shipping\n"
    "  Subtotal: 10.97 yuan\n"
    "  Shipping: 5.00 yuan\n"
    "  Total: 15.97 yuan\n"
    "Free shipping\n"
    "  Subtotal: 50.00 yuan\n"
    "  Shipping: 0.00 yuan\n"
    "  Total: 50.00 yuan\n"
    "Large amount: 90071992547409.93 yuan\n"
)


class MoneyDemoTests(unittest.TestCase):
    def check_output(self, command, cwd):
        self.assertTrue(SCRIPT.is_file(), "The runnable example must exist")
        result = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, EXPECTED_OUTPUT)
        self.assertEqual(result.stderr, "")

    def test_runs_with_python_from_repository_root(self):
        self.check_output([sys.executable, str(SCRIPT)], ROOT)

    def test_runs_with_python_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            self.check_output([sys.executable, str(SCRIPT)], directory)

    @unittest.skipUnless(os.name == "posix", "Direct execution uses a POSIX shebang")
    def test_runs_directly_from_another_directory(self):
        self.assertTrue(os.access(SCRIPT, os.X_OK), "The example must be executable")
        with tempfile.TemporaryDirectory() as directory:
            self.check_output([str(SCRIPT)], directory)

    def test_import_has_no_output(self):
        self.assertTrue(SCRIPT.is_file(), "The runnable example must exist")
        result = subprocess.run(
            [sys.executable, "-c", "import money_demo"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
