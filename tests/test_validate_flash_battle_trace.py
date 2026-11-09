"""Regression tests for Flash battle trace structural validation."""
import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_flash_battle_trace import validate


class BattleTraceValidationTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(schema_version=1, source="flash", case_id="win_001",
                        step=0, action="initial", floor=0, x=0, y=0,
                        hp=None, money=None, exp=None, monster_id=None,
                        monster_present=None, battle_phase=None, game_over=None,
                        evidence_frame=None, verified=False)

    def check(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "trace.jsonl"
            path.write_text("\n".join(json.dumps(row) for row in rows),
                            encoding="utf-8")
            return validate(path)

    def test_unverified_nulls_allowed(self):
        self.assertEqual(self.check([self.row]), [])

    def test_rejects_verified_without_evidence(self):
        self.row["verified"] = True
        self.assertTrue(self.check([self.row]))

    def test_rejects_verified_without_observed_state(self):
        self.row.update(verified=True, evidence_frame="frames/0001.png",
                        floor=None, x=None, y=None)
        self.assertTrue(self.check([self.row]))

    def test_rejects_nonstring_evidence_frame(self):
        self.row["evidence_frame"] = True
        self.assertTrue(self.check([self.row]))

    def test_rejects_blank_evidence_frame(self):
        self.row["evidence_frame"] = "   "
        self.assertTrue(self.check([self.row]))

    def test_accepts_verified_with_observation_and_frame(self):
        self.row.update(verified=True, evidence_frame="frames/0001.png", hp=100)
        self.assertEqual(self.check([self.row]), [])

    def test_rejects_invalid_battle_phase_type(self):
        self.row["battle_phase"] = []
        self.assertTrue(self.check([self.row]))

    def test_rejects_boolean_monster_id(self):
        self.row["monster_id"] = False
        self.assertTrue(self.check([self.row]))

    def test_rejects_skipped_step(self):
        self.assertTrue(self.check([self.row, dict(self.row, step=2)]))

    def test_rejects_mixed_sources(self):
        self.assertTrue(self.check([self.row, dict(self.row, step=1, source="html5")]))

    def test_rejects_boolean_as_hp(self):
        self.row["hp"] = False
        self.assertTrue(self.check([self.row]))

    def test_rejects_missing_field(self):
        del self.row["hp"]
        self.assertTrue(self.check([self.row]))

    def test_rejects_empty_trace(self):
        self.assertTrue(self.check([]))

    def test_rejects_invalid_source_type(self):
        self.row["source"] = []
        self.assertTrue(self.check([self.row]))


if __name__ == "__main__":
    unittest.main()
