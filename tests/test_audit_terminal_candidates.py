"""Fail-closed tests for original Flash terminal-path candidate inventory."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import audit_terminal_candidates as audit


class TerminalCandidatesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.swf = b"synthetic SWF for unit tests"
        self.sha = hashlib.sha256(self.swf).hexdigest()
        self.pin = patch.object(audit, "SWF_SHA256", self.sha)
        self.pin.start()
        self.addCleanup(self.pin.stop)
        self.script = "if (_root.Now_hp <= 0) { gotoAndStop('game_over'); }\n"
        self.path = "scripts/frame_1/DoAction.as"
        self.file = self.root / self.path
        self.file.parent.mkdir(parents=True)
        self.file.write_text(self.script, encoding="utf-8")
        self.manifest = {"original": {"sha256": self.sha}, "files": [
            {"path": self.path, "sha256": hashlib.sha256(self.script.encode()).hexdigest(),
             "size": len(self.script.encode())}
        ]}

    def test_reports_source_linked_candidates_without_runtime_claims(self):
        result = audit.audit_candidates(self.manifest, self.root, self.swf)
        self.assertEqual(result["script_files_checked"], 1)
        self.assertEqual(result["candidate_counts"],
                         {"game_over_mention": 1, "hero_hp_comparison": 1})
        self.assertEqual(result["candidates"][0]["line"], 1)
        self.assertFalse(result["death_behavior_verified"])
        self.assertFalse(result["ending_verified"])
        self.assertFalse(result["gymnasium_ready"])

    def test_source_context_is_bounded_and_source_hashed(self):
        lines = ["trace('padding');"] * 45
        lines[29] = '_root.gotoAndPlay("game_over");'
        lines[41] = '_root.gotoAndPlay("game_over");'
        data = ("\\n".join(lines) + "\\n").encode("utf-8")
        self.file.write_bytes(data)
        self.manifest["files"][0].update(
            sha256=hashlib.sha256(data).hexdigest(), size=len(data)
        )
        result = audit.audit_candidates(self.manifest, self.root, self.swf)
        self.assertEqual(result["candidate_counts"]["game_over_mention"], 2)
        hits = [h for h in result["candidates"] if h["kind"] == "game_over_mention"]
        self.assertEqual([h["line"] for h in hits], [30, 42])
        self.assertEqual([row["line"] for row in hits[0]["source_context"]], list(range(6, 39)))
        self.assertEqual([row["line"] for row in hits[1]["source_context"]], list(range(18, 46)))
        self.assertEqual(hits[0]["source_context"][24]["text"], lines[29])
        self.assertEqual(hits[1]["source_sha256"], hashlib.sha256(data).hexdigest())
        self.assertFalse(result["death_behavior_verified"])
        self.assertFalse(result["ending_verified"])

    def test_context_marks_long_lines_as_truncated(self):
        data = ("game_over " + "x" * 500 + "\\n").encode("utf-8")
        self.file.write_bytes(data)
        self.manifest["files"][0].update(
            sha256=hashlib.sha256(data).hexdigest(), size=len(data)
        )
        result = audit.audit_candidates(self.manifest, self.root, self.swf)
        row = result["candidates"][0]["source_context"][0]
        self.assertEqual(len(row["text"]), 400)
        self.assertTrue(row["truncated"])
        self.assertEqual(row["line"], 1)

    def test_rejects_wrong_swf_bytes(self):
        with self.assertRaisesRegex(ValueError, "game.swf"):
            audit.audit_candidates(self.manifest, self.root, b"changed")

    def test_rejects_wrong_manifest_source(self):
        self.manifest["original"]["sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "manifest SWF"):
            audit.audit_candidates(self.manifest, self.root, self.swf)

    def test_rejects_modified_actionscript(self):
        self.file.write_text(self.script + "extra", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            audit.audit_candidates(self.manifest, self.root, self.swf)

    def test_rejects_unlisted_actionscript(self):
        (self.root / "scripts/extra.as").write_text("trace('extra');", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "inventory differs"):
            audit.audit_candidates(self.manifest, self.root, self.swf)

    def test_rejects_missing_actionscript(self):
        self.file.unlink()
        with self.assertRaisesRegex(ValueError, "inventory differs"):
            audit.audit_candidates(self.manifest, self.root, self.swf)

    def test_no_game_over_text_does_not_fake_an_ending(self):
        data = b"if (_root.right_hp < 0) { trace('hp'); }"
        self.file.write_bytes(data)
        self.manifest["files"][0].update(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
        result = audit.audit_candidates(self.manifest, self.root, self.swf)
        self.assertEqual(result["candidate_counts"]["game_over_mention"], 0)
        self.assertEqual(result["candidate_counts"]["hero_hp_comparison"], 1)
        self.assertFalse(result["ending_verified"])


if __name__ == "__main__":
    unittest.main()
