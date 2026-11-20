"""Strict evidence-file verification regression tests."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.check_battle_evidence_files import check


class EvidenceFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.trace = self.root / "trace.jsonl"

    def verify(self, frame, verified=True):
        self.trace.write_text(json.dumps({"verified": verified, "evidence_frame": frame}))
        return check(self.trace, self.root)

    def test_existing_file(self):
        (self.root / "frames").mkdir()
        (self.root / "frames" / "a.png").write_bytes(b"example")
        self.assertEqual(self.verify("frames/a.png"), [])

    def test_missing_file(self):
        self.assertTrue(self.verify("frames/missing.png"))

    def test_absolute_path(self):
        self.assertTrue(self.verify("/tmp/frame.png"))

    def test_parent_traversal(self):
        self.assertTrue(self.verify("../frame.png"))

    def test_windows_path(self):
        self.assertTrue(self.verify("C:\\temp\\frame.png"))

    def test_unverified_legacy_record(self):
        self.assertEqual(self.verify(None, False), [])

    def test_missing_verified_frame(self):
        self.assertTrue(self.verify(None))

    def test_empty_trace(self):
        self.trace.write_text("")
        self.assertTrue(check(self.trace, self.root))


    def test_duplicate_verified_key_rejected(self):
        self.trace.write_text('{"verified":true,"verified":false,"evidence_frame":"missing.png"}')
        self.assertTrue(check(self.trace, self.root))

    def test_duplicate_nested_key_rejected(self):
        self.trace.write_text('{"verified":false,"metadata":{"a":1,"a":2}}')
        self.assertTrue(check(self.trace, self.root))

    def test_nonfinite_json_rejected(self):
        self.trace.write_text('{"verified":false,"value":NaN}')
        self.assertTrue(check(self.trace, self.root))

if __name__ == "__main__":
    unittest.main()
