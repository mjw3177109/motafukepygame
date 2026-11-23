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
            # Zero fresh files must still fail closed, but write a clean manifest.
            with self.assertRaises(SystemExit):
                self.invoke(swf, jar, out)
            report = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
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


    def test_nested_symlink_file_is_rejected_without_reading_external_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            swf, jar, out = root / "game.swf", root / "ffdec.jar", root / "audit"
            swf.write_bytes(b"fake")
            jar.write_bytes(b"fake")
            external = root / "secret.as"
            external.write_text("not from swf")
            def fake_ffdec(_jar, argv, _logfile):
                if "-export" in argv:
                    nested = out / "export" / "scripts"
                    nested.mkdir(parents=True)
                    (nested / "good.as").write_text("fresh")
                    (nested / "bad.as").symlink_to(external)
                return {"exit_code": 0}
            with patch.object(sys, "argv", [
                "extract_swf.py", "--swf", str(swf), "--ffdec", str(jar), "--out", str(out)
            ]), patch.object(extract_swf, "probe", return_value={"sha256": "test-source"}), patch.object(
                extract_swf, "run_ffdec", side_effect=fake_ffdec
            ):
                with self.assertRaisesRegex(SystemExit, "symlink"):
                    extract_swf.main()
            self.assertEqual(external.read_text(), "not from swf")
            self.assertFalse((out / "manifest.json").exists())

    def test_dangling_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            swf, jar, out = root / "game.swf", root / "ffdec.jar", root / "audit"
            swf.write_bytes(b"fake")
            jar.write_bytes(b"fake")
            def fake_ffdec(_jar, argv, _logfile):
                if "-export" in argv:
                    folder = out / "export"
                    folder.mkdir(parents=True)
                    (folder / "missing.as").symlink_to(root / "nonexistent.as")
                return {"exit_code": 0}
            with patch.object(sys, "argv", [
                "extract_swf.py", "--swf", str(swf), "--ffdec", str(jar), "--out", str(out)
            ]), patch.object(extract_swf, "probe", return_value={"sha256": "test-source"}), patch.object(
                extract_swf, "run_ffdec", side_effect=fake_ffdec
            ):
                with self.assertRaisesRegex(SystemExit, "symlink"):
                    extract_swf.main()


if __name__ == "__main__":
    unittest.main()
