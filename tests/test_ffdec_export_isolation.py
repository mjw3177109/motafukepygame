"""Regression tests: FFDec export inventory must not include stale artifacts."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import extract_swf


class ExportIsolationTests(unittest.TestCase):
    def invoke(self, swf, jar, out, metadata_only=False):
        argv = ["extract_swf.py", "--swf", str(swf), "--ffdec", str(jar), "--out", str(out)]
        if metadata_only:
            argv.append("--metadata-only")
        with patch.object(sys, "argv", argv), patch.object(
            extract_swf, "probe", return_value={"sha256": "test-source"}
        ), patch.object(
            extract_swf, "run_ffdec", return_value={"exit_code": 0}
        ):
            extract_swf.main()
        return json.loads((out / "manifest.json").read_text(encoding="utf-8"))

    def test_stale_export_is_removed_before_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            swf, jar, out = root / "game.swf", root / "ffdec.jar", root / "audit"
            swf.write_bytes(b"fake")
            jar.write_bytes(b"fake")
            (out / "export").mkdir(parents=True)
            (out / "export" / "stale.as").write_text("old")
            report = self.invoke(swf, jar, out)
            self.assertFalse((out / "export" / "stale.as").exists())
            self.assertEqual(report["exported_file_count"], 0)
            self.assertEqual(report["files"], [])

    def test_metadata_only_does_not_inventory_old_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            swf, jar, out = root / "game.swf", root / "ffdec.jar", root / "audit"
            swf.write_bytes(b"fake")
            jar.write_bytes(b"fake")
            (out / "export").mkdir(parents=True)
            (out / "export" / "old.as").write_text("old")
            report = self.invoke(swf, jar, out, metadata_only=True)
            self.assertTrue((out / "export" / "old.as").exists())
            self.assertEqual(report["exported_file_count"], 0)

    def test_symlink_export_is_rejected_without_deleting_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            swf, jar, out = root / "game.swf", root / "ffdec.jar", root / "audit"
            swf.write_bytes(b"fake")
            jar.write_bytes(b"fake")
            out.mkdir()
            target = root / "external"
            target.mkdir()
            (target / "keep.txt").write_text("keep")
            (out / "export").symlink_to(target, target_is_directory=True)
            with self.assertRaises(SystemExit):
                self.invoke(swf, jar, out)
            self.assertEqual((target / "keep.txt").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
