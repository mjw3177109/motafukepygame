import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from preserve_ffdec_drift import preserve


class PreserveDriftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.first, self.second, self.out = (self.base / x for x in ("a", "b", "out"))
        self.first.mkdir()
        self.second.mkdir()
        self.report = self.base / "report.json"

    def run_case(self, paths):
        self.report.write_text(json.dumps({"changed": paths}), encoding="utf-8")
        return preserve(self.report, self.first, self.second, self.out)

    def test_preserves_all_changed_scripts(self):
        for name in ("frame_3/DoAction.as", "frame_4/DoAction.as"):
            for root, data in ((self.first, b"one"), (self.second, b"two")):
                f = root / name
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(data)
        self.assertEqual(self.run_case(["frame_3/DoAction.as", "frame_4/DoAction.as"]), 2)
        self.assertEqual((self.out / "first/frame_3/DoAction.as").read_bytes(), b"one")
        self.assertEqual((self.out / "second/frame_4/DoAction.as").read_bytes(), b"two")

    def test_rejects_traversal(self):
        with self.assertRaises(ValueError):
            self.run_case(["../outside"])

    def test_rejects_absolute(self):
        with self.assertRaises(ValueError):
            self.run_case(["/tmp/a"])

    def test_rejects_duplicate(self):
        with self.assertRaises(ValueError):
            self.run_case(["x", "x"])

    def test_rejects_missing_before_writes(self):
        with self.assertRaises(ValueError):
            self.run_case(["missing"])
        self.assertFalse(self.out.exists())

    def test_rejects_output_inside_source(self):
        self.report.write_text('{"changed": []}', encoding="utf-8")
        with self.assertRaises(ValueError):
            preserve(self.report, self.first, self.second, self.first / "evidence")


if __name__ == "__main__":
    unittest.main()
