"""Fail-closed tile-24 handoff -> source-audited review bridge regression."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from test_audit_tile24_branch_order import SOURCE
from core.tile24_handoff_preview import preview_tile24_handoff

CASES = json.loads((Path(__file__).parent / "fixtures" / "tile24_state_cases.json").read_text(encoding="utf-8"))


def world(tile=24, blocked=False):
    grid = [[0] * 11 for _ in range(11)]
    grid[5][6] = tile
    return {"grid": grid, "row": 5, "col": 5,
            "keys": {"yellow": 0, "blue": 0, "red": 0},
            "key_flag": 0 if blocked else 1, "display_list": 0,
            "display_jump": 0, "display_text": 0, "display_buy": 0,
            "display_kill": 0}


class Tile24HandoffPreviewTests(unittest.TestCase):
    def test_source_gated_preview_keeps_world_and_review_state_unchanged(self):
        w = world()
        review = deepcopy(next(c["input"] for c in CASES if c["name"] == "three_independent_guards"))
        before_world, before_review = deepcopy(w), deepcopy(review)
        result = preview_tile24_handoff(w, 2, {}, review, SOURCE)
        self.assertEqual(result["target"], [5, 6])
        self.assertEqual(result["event"], "tile24_review_only")
        self.assertEqual([x["branch"] for x in result["review"]["trace"]],
                         ["initial_dialogue", "ending_state_change", "floor22_dialogue"])
        self.assertEqual(len([x for x in result["review"]["trace"] if "clip_command" in x]), 2)
        self.assertTrue(result["review"]["source_branch_order_verified"])
        for field in ("state_mapping_verified", "flash_runtime_verified", "executable", "gymnasium_ready"):
            self.assertFalse(result[field])
        self.assertEqual(w, before_world)
        self.assertEqual(review, before_review)

    def test_blocked_non_event_and_malformed_review_fail_closed(self):
        review = deepcopy(CASES[1]["input"])
        for w in (world(blocked=True), world(tile=0)):
            before = deepcopy(w)
            with self.assertRaisesRegex(ValueError, "no tile-24 handoff"):
                preview_tile24_handoff(w, 2, {}, review, SOURCE)
            self.assertEqual(w, before)
        w = world()
        for invalid in ({**review, "tile_id": 129}, {**review, "get_money": [1, 1]}):
            before = deepcopy(w)
            with self.assertRaises(ValueError):
                preview_tile24_handoff(w, 2, {}, invalid, SOURCE)
            self.assertEqual(w, before)
        with self.assertRaises(ValueError):
            preview_tile24_handoff(w, 2, {}, review,
                                   SOURCE.replace("_root.mt_changes == 1 &&", "_root.mt_changes == 2 &&"))


if __name__ == "__main__":
    unittest.main()
