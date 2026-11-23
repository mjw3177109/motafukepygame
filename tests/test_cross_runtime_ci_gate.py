"""Fail closed when CI cannot execute the Python/JavaScript parity contract.

The shared-vector test intentionally permits local Python-only development, but
CI must not report green while skipping the JavaScript comparison.
"""
import os
import shutil
import unittest


class CrossRuntimeCIGateTests(unittest.TestCase):
    def test_node_is_available_when_running_in_ci(self):
        if os.environ.get("CI", "").lower() == "true":
            self.assertIsNotNone(
                shutil.which("node"),
                "CI must install Node.js: skipping cross-runtime parity is not allowed",
            )


if __name__ == "__main__":
    unittest.main()
