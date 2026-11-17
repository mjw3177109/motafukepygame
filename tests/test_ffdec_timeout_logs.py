"""Regression coverage for FFDec subprocess timeout diagnostics."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from extract_swf import run_ffdec


class FFDecTimeoutTests(unittest.TestCase):
    def test_timeout_preserves_partial_binary_output(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "ffdec.log"
            timeout = subprocess.TimeoutExpired(
                ["java"], 3, output=b"partial\\xff", stderr=b"error"
            )
            with patch("extract_swf.subprocess.run", side_effect=timeout):
                result = run_ffdec(Path("ffdec.jar"), [], log)
            self.assertEqual(result["exit_code"], 124)
            text = log.read_text(encoding="utf-8")
            self.assertIn("partial\\ufffd", text)
            self.assertIn("error", text)

    def test_timeout_preserves_text_output_with_missing_stderr(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "ffdec.log"
            timeout = subprocess.TimeoutExpired(
                ["java"], 3, output="partial", stderr=None
            )
            with patch("extract_swf.subprocess.run", side_effect=timeout):
                result = run_ffdec(Path("ffdec.jar"), [], log)
            self.assertEqual(result["exit_code"], 124)
            self.assertIn("partial", log.read_text(encoding="utf-8"))

    def test_nonzero_exit_still_records_stderr(self):
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "ffdec.log"
            completed = subprocess.CompletedProcess([], 2, "stdout", "stderr")
            with patch("extract_swf.subprocess.run", return_value=completed):
                result = run_ffdec(Path("ffdec.jar"), [], log)
            self.assertEqual(result["exit_code"], 2)
            self.assertIn("stderr", log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
