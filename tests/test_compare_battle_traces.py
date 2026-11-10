"""Fail-closed comparisons against an independently supplied Flash trace."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.compare_battle_traces import compare


class CompareBattleTracesTests(unittest.TestCase):
    def setUp(self):
        self.flash = dict(schema_version=1, source="flash", case_id="win_001", step=0,
                          action="initial", floor=0, x=1, y=2, hp=100, money=0,
                          exp=0, monster_id="1", monster_present=True,
                          battle_phase="idle", game_over=False,
                          evidence_frame="flash/0.png", verified=True)
        self.candidate = dict(self.flash, source="pygame", evidence_frame="pygame/0.png")

    def run_compare(self, flash=None, candidate=None):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "flash.jsonl", Path(folder) / "candidate.jsonl"
            a.write_text("\n".join(json.dumps(x) for x in (flash if flash is not None else [self.flash])), encoding="utf-8")
            b.write_text("\n".join(json.dumps(x) for x in (candidate if candidate is not None else [self.candidate])), encoding="utf-8")
            return compare(a, b)

    def test_matching_observations(self):
        self.assertEqual(self.run_compare(), [])

    def test_html5_allowed(self):
        self.candidate["source"] = "html5"
        self.assertEqual(self.run_compare(), [])

    def test_rejects_unverified_reference(self):
        self.flash["verified"] = False
        self.assertIn("unverified", str(self.run_compare()))

    def test_rejects_missing_state(self):
        self.flash["hp"] = None
        self.assertIn("not observed", str(self.run_compare()))

    def test_rejects_wrong_reference(self):
        self.flash["source"] = "pygame"
        self.assertIn("original Flash", str(self.run_compare()))

    def test_rejects_hp_mismatch(self):
        self.candidate["hp"] = 99
        self.assertIn("hp differs", str(self.run_compare()))

    def test_rejects_action_mismatch(self):
        self.candidate["action"] = "left"
        self.assertIn("case/action mismatch", str(self.run_compare()))

    def test_rejects_missing_step(self):
        self.assertIn("empty trace", str(self.run_compare(candidate=[])))


if __name__ == "__main__":
    unittest.main()
