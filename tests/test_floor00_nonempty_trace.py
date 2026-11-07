"""Non-empty floor-00 CLI integration regression; source-pinned map only.

This is a deterministic probe, not proof of Flash gameplay parity.
"""
import json
import unittest

from core.movement_probe import DELTAS
from tools.floor00_trace_cli import run


class Floor00NonemptyTraceTests(unittest.TestCase):
    def test_one_step_on_original_floor_without_unsupported_events(self):
        keys = {"yellow": 0, "blue": 0, "red": 0}
        initial = json.loads(run({"keys": keys, "arrow_ids": []}))["initial_state"]
        row, col, grid = initial["row"], initial["col"], initial["grid"]
        # Pick an adjacent boundary or wall from the *committed original map*.
        # Never substitute a synthetic tile or assume an unverified event.
        candidates = [
            direction for direction, (dr, dc) in DELTAS.items()
            if not (0 <= row + dr < 11 and 0 <= col + dc < 11)
            or grid[row + dr][col + dc] == 1
        ]
        if not candidates:
            self.skipTest("original spawn has no adjacent wall/boundary; no fabricated move")
        direction = candidates[0]
        result = json.loads(run({"keys": keys, "arrow_ids": [direction]}))
        self.assertEqual(len(result["frames"]), 1)
        self.assertEqual(result["frames"][0]["arrow_id"], direction)
        self.assertIn(result["frames"][0]["event"], ("wall", "boundary"))
        self.assertEqual(result["initial_state"], initial)
        self.assertEqual(result["final_state"], initial)
        self.assertEqual(result["frames"][0]["state"], initial)

    def test_invalid_nonempty_direction_fails_closed(self):
        with self.assertRaises(ValueError):
            run({"keys": {"yellow": 0, "blue": 0, "red": 0}, "arrow_ids": [0]})


if __name__ == "__main__":
    unittest.main()
