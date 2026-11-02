"""Synthetic fixtures for source-checked say-08 handoff; not Flash parity."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import audit_say08_handoff as handoff
from tools import audit_terminal_candidates as base


class Say08HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.swf = b"synthetic SWF"
        self.sha = hashlib.sha256(self.swf).hexdigest()
        pin = patch.object(base, "SWF_SHA256", self.sha)
        pin.start()
        self.addCleanup(pin.stop)
        self.sources = {
            f"scripts/DefineSprite_795_mt_say_08/frame_{frame}/DoAction.as":
            f"_root.Display_say[8] = {value};\n"
            for frame, value in handoff.WRITERS.items()
        }
        self.sources[handoff.CONSUMER] = """if(_root.Display_say[8] == 2)
{
  _root.DelMovie("mtsay_008");
  _root.Display_say[8] = 3;
  _root.Now_key_flag = 1;
}
if(_root.Display_say[8] == 5)
{
  _root.DelMovie("mtsay_008");
  _root.Display_say[8] = 6;
  _root.Now_key_flag = 1;
}
if(_root.Display_say[8] == 9)
{
  _root.DelMovie("mtsay_008");
  _root.Display_say[8] = 10;
  _root.Now_key_flag = 1;
  if(_root.mt_LastGame_ID == 0)
  {
    _root.DelBaseDisplay();
    _root.DelLineDisplay();
    _root.gotoAndPlay("game_over");
  }
  if(_root.mt_LastGame_ID == 1)
  {
    _root.mt_line_21[1][5] = 13;
  }
}
"""

    def manifest(self):
        files = []
        for path, content in self.sources.items():
            file = self.root / path
            file.parent.mkdir(parents=True, exist_ok=True)
            raw = content.encode()
            file.write_bytes(raw)
            files.append({"path": path, "size": len(raw),
                          "sha256": hashlib.sha256(raw).hexdigest()})
        return {"original": {"sha256": self.sha}, "files": files}

    def test_source_handoff_is_evidence_not_runtime(self):
        report = handoff.audit_handoff(self.manifest(), self.root, self.swf)
        self.assertEqual([w["value"] for w in report["writers"]], [2, 5, 9])
        self.assertEqual([(x["input"], x["output"]) for x in
                          report["consumer"]["state_transitions"]],
                         [(2, 3), (5, 6), (9, 10)])
        self.assertTrue(report["source_manifest_verified"])
        self.assertFalse(report["execution_order_verified"])
        self.assertFalse(report["ending_verified"])
        self.assertFalse(report["gymnasium_ready"])

    def test_crlf_ffdec_frame_write_is_accepted(self):
        for path in list(self.sources):
            self.sources[path] = self.sources[path].replace("\n", "\r\n")
        report = handoff.audit_handoff(self.manifest(), self.root, self.swf)
        self.assertEqual([x["value"] for x in report["writers"]], [2, 5, 9])

    def test_missing_frame_write_fails_closed(self):
        path = "scripts/DefineSprite_795_mt_say_08/frame_12/DoAction.as"
        self.sources[path] = "_root.Display_say[8] = 8;\n"
        with self.assertRaisesRegex(ValueError, "frame 12 write"):
            handoff.audit_handoff(self.manifest(), self.root, self.swf)

    def test_missing_terminal_guard_fails_closed(self):
        self.sources[handoff.CONSUMER] = self.sources[handoff.CONSUMER].replace(
            "mt_LastGame_ID == 0", "mt_LastGame_ID == 2")
        with self.assertRaisesRegex(ValueError, "terminal conditional"):
            handoff.audit_handoff(self.manifest(), self.root, self.swf)

    def test_manifest_tampering_fails_closed(self):
        manifest = self.manifest()
        path = self.root / handoff.CONSUMER
        path.write_text(path.read_text().replace("== 9", "== 8"))
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            handoff.audit_handoff(manifest, self.root, self.swf)

    def test_wrong_swf_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            handoff.audit_handoff(self.manifest(), self.root, b"wrong")


    def test_indexes_original_guard_write_candidates_with_hash_and_context(self):
        path = "scripts/frame_4346/DoAction_2.as"
        self.sources[path] = (
            "mt_LastGame_ID = 0;\n"
            "_root.mt_LastGame_ID += 1;\n"
            "if(mt_LastGame_ID == 0) {}\n"
            "Display_say[8] = 9;\n"
        )
        report = handoff.audit_handoff(self.manifest(), self.root, self.swf)
        guard = report["terminal_guard"]
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(guard["variable"], "mt_LastGame_ID")
        self.assertEqual(guard["write_candidate_count"], 2)
        self.assertEqual([hit["line"] for hit in guard["write_candidates"]], [1, 2])
        self.assertEqual([hit["operator"] for hit in guard["write_candidates"]], ["=", "+="])
        self.assertEqual([hit["target"] for hit in guard["write_candidates"]],
                         ["mt_LastGame_ID", "_root.mt_LastGame_ID"])
        self.assertTrue(all(hit["path"] == path for hit in guard["write_candidates"]))
        self.assertTrue(all(len(hit["source_sha256"]) == 64 for hit in guard["write_candidates"]))
        self.assertTrue(all(hit["source_context"] for hit in guard["write_candidates"]))
        self.assertTrue(guard["source_writes_are_text_candidates_only"])
        self.assertFalse(guard["runtime_value_proven"])
        self.assertFalse(report["ending_verified"])

    def test_no_guard_write_candidate_does_not_infer_runtime_default(self):
        report = handoff.audit_handoff(self.manifest(), self.root, self.swf)
        self.assertEqual(report["terminal_guard"]["write_candidate_count"], 0)
        self.assertEqual(report["terminal_guard"]["write_candidates"], [])
        self.assertFalse(report["terminal_guard"]["runtime_value_proven"])


if __name__ == "__main__":
    unittest.main()
