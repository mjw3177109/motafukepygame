"""Regression coverage for one-sided FFDec export evidence."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from preserve_ffdec_drift import preserve


class OneSidedDriftTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.first = self.root / "first"
        self.second = self.root / "second"
        self.out = self.root / "evidence"
        self.first.mkdir()
        self.second.mkdir()
        self.report = self.root / "report.json"

    def run_report(self, data):
        self.report.write_text(json.dumps(data), encoding="utf-8")
        return preserve(self.report, self.first, self.second, self.out)

    def test_preserves_only_first_and_only_second(self):
        (self.first / "first_only.as").write_bytes(b"FIRST")
        (self.second / "second_only.as").write_bytes(b"SECOND")
        count = self.run_report({
            "changed": [], "only_first": ["first_only.as"],
            "only_second": ["second_only.as"],
        })
        self.assertEqual(count, 2)
        self.assertEqual((self.out / "first/first_only.as").read_bytes(), b"FIRST")
        self.assertEqual((self.out / "second/second_only.as").read_bytes(), b"SECOND")
        self.assertFalse((self.out / "second/first_only.as").exists())
        self.assertFalse((self.out / "first/second_only.as").exists())

    def test_rejects_cross_category_overlap_before_writing(self):
        (self.first / "same.as").write_bytes(b"A")
        (self.second / "same.as").write_bytes(b"B")
        with self.assertRaises(ValueError):
            self.run_report({"changed": ["same.as"], "only_first": ["same.as"]})
        self.assertFalse(self.out.exists())

    def test_rejects_missing_one_sided_file_before_writing(self):
        (self.first / "exists.as").write_bytes(b"ok")
        with self.assertRaises(ValueError):
            self.run_report({
                "changed": [], "only_first": ["exists.as"],
                "only_second": ["missing.as"],
            })
        self.assertFalse(self.out.exists())

    def test_rejects_traversal_in_one_sided_category(self):
        with self.assertRaises(ValueError):
            self.run_report({"changed": [], "only_first": ["../escape.as"]})
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
