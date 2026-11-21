"""Source-hashed terminal-state write candidates; never infer runtime branches."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import audit_terminal_candidates as audit


class TerminalStateWritesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.swf = b"synthetic SWF"
        self.sha = hashlib.sha256(self.swf).hexdigest()
        pin = patch.object(audit, "SWF_SHA256", self.sha)
        pin.start()
        self.addCleanup(pin.stop)
        self.path = "scripts/frame_1/DoAction.as"
        self.file = self.root / self.path
        self.file.parent.mkdir(parents=True)

    def check(self, source):
        raw = source.encode("utf-8")
        self.file.write_bytes(raw)
        manifest = {"original": {"sha256": self.sha}, "files": [{
            "path": self.path, "sha256": hashlib.sha256(raw).hexdigest(),
            "size": len(raw),
        }]}
        return audit.audit_candidates(manifest, self.root, self.swf), manifest

    def test_indexes_exact_state_writes_and_array_resets(self):
        result, _ = self.check("""Display_text = 2;
Display_say[8] = 10;
_root.mt_LastGame_ID += 1;
mt_line_26[3][5] = 0;
Display_say = [];
""")
        writes = [h for h in result["candidates"] if h["kind"] == "terminal_state_write"]
        self.assertEqual(result["state_write_candidate_count"], 5)
        self.assertEqual([h["line"] for h in writes], [1, 2, 3, 4, 5])
        self.assertEqual([h["operator"] for h in writes], ["=", "=", "+=", "=", "="])
        self.assertEqual(writes[2]["target"], "_root.mt_LastGame_ID")
        self.assertEqual(result["schema_version"], 2)
        self.assertTrue(result["state_writes_are_text_candidates_not_proven_assignments"])
        self.assertFalse(result["ending_verified"])
        self.assertFalse(result["gymnasium_ready"])

    def test_does_not_confuse_conditions_with_writes(self):
        result, _ = self.check("""Display_text == 2;
Display_say[8] === 9;
mt_LastGame_ID != 0;
mt_line_26[3][5] <= 1;
""")
        self.assertEqual(result["state_write_candidate_count"], 0)

    def test_dynamic_index_and_increment_are_candidates_only(self):
        result, _ = self.check("""Display_say[i]++;
mt_line_26[x][y] -= 1;
""")
        self.assertEqual(result["state_write_candidate_count"], 2)
        self.assertEqual([h["operator"] for h in result["candidates"]], ["++", "-="])
        self.assertFalse(result["flash_runtime_verified"])

    def test_multiple_writes_on_one_line_are_all_indexed(self):
        source = ("Display_text = 2; Display_say[8] = 9; "
                  "mt_LastGame_ID++; mt_line_26[3][5] = 0;\\n")
        result, _ = self.check(source)
        writes = [h for h in result["candidates"] if h["kind"] == "terminal_state_write"]
        self.assertEqual(result["state_write_candidate_count"], 4)
        self.assertEqual([h["target"] for h in writes], [
            "Display_text", "Display_say[8]", "mt_LastGame_ID", "mt_line_26[3][5]"
        ])
        self.assertEqual([h["column"] for h in writes], [
            source.index(h["target"]) + 1 for h in writes
        ])
        self.assertEqual([h["line"] for h in writes], [1] * 4)

    def test_repeated_target_on_same_line_keeps_both_writes(self):
        source = "Display_say[8] = 2; Display_say[8] = 9;\\n"
        result, _ = self.check(source)
        writes = [h for h in result["candidates"] if h["kind"] == "terminal_state_write"]
        self.assertEqual(result["state_write_candidate_count"], 2)
        self.assertEqual([h["column"] for h in writes], [1, source.rindex("Display_say") + 1])
        self.assertEqual([h["operator"] for h in writes], ["=", "="])

    def test_non_write_mentions_remain_line_deduplicated(self):
        result, _ = self.check("game_over game_over; Now_hp <= 0 || right_hp > 0;\\n")
        self.assertEqual(result["candidate_counts"], {
            "game_over_mention": 1, "hero_hp_comparison": 1
        })
        self.assertEqual(result["state_write_candidate_count"], 0)

    def test_tampered_source_fails_closed(self):
        _, manifest = self.check("Display_text = 2;\n")
        self.file.write_text("Display_text = 3;\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            audit.audit_candidates(manifest, self.root, self.swf)


if __name__ == "__main__":
    unittest.main()
