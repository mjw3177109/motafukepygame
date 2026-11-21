"""Fail-closed regression tests for original shop export comparison."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools import audit_shop_exports
from tools.audit_shop_exports import audit, RELATIVE


class ShopExportAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.first, self.second = self.root / "first", self.root / "second"
        self.swf = self.root / "game.swf"
        self.swf.write_bytes(b"not the original SWF")
        for frame in (2, 4):
            for root in (self.first, self.second):
                p = root / RELATIVE.format(frame=frame)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(f"frame {frame}".encode())

    def test_failed_rerun_removes_stale_success_report(self):
        report = self.root / 'shop_export_audit.json'
        report.write_text('{"independent_exports_identical": true}', encoding='utf-8')
        argv = ['audit_shop_exports', '--first', str(self.first), '--second', str(self.second),
                '--swf', str(self.swf), '--out', str(report)]
        with patch.object(sys, 'argv', argv):
            with self.assertRaises(SystemExit) as caught:
                audit_shop_exports.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertFalse(report.exists())

    def test_report_path_cannot_destroy_original_inputs(self):
        for target in (self.swf, self.first / RELATIVE.format(frame=2),
                       self.second / RELATIVE.format(frame=4)):
            before = target.read_bytes()
            argv = ['audit_shop_exports', '--first', str(self.first), '--second', str(self.second),
                    '--swf', str(self.swf), '--out', str(target)]
            with self.subTest(target=target):
                with patch.object(sys, 'argv', argv):
                    with self.assertRaises(SystemExit) as caught:
                        audit_shop_exports.main()
                self.assertEqual(caught.exception.code, 2)
                self.assertEqual(target.read_bytes(), before)

    def test_rejects_nonoriginal_swf(self):
        with self.assertRaisesRegex(ValueError, "game.swf SHA256 mismatch"):
            audit(self.first, self.second, self.swf)

    def test_rejects_drift_missing_and_empty(self):
        with patch.object(audit_shop_exports, "SWF_SHA256",
                          hashlib.sha256(self.swf.read_bytes()).hexdigest()):
            report = audit(self.first, self.second, self.swf)
            self.assertFalse(report["shop_behavior_verified"])
            self.assertFalse(report["actionrecord_verified"])
            p = self.second / RELATIVE.format(frame=4)
            p.write_bytes(b"drift")
            with self.assertRaisesRegex(ValueError, "exports differ"):
                audit(self.first, self.second, self.swf)
            p.unlink()
            with self.assertRaisesRegex(ValueError, "missing independent"):
                audit(self.first, self.second, self.swf)
            p.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "empty or whitespace-only export"):
                audit(self.first, self.second, self.swf)
            p.write_bytes(b" \t\n")
            with self.assertRaisesRegex(ValueError, "whitespace-only export"):
                audit(self.first, self.second, self.swf)


if __name__ == "__main__":
    unittest.main()
