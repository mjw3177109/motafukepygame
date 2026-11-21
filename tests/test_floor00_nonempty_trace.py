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
        # Select an actual walkable neighbor from the pinned source map.
        # Fail rather than silently skip when the source fixture changes.
        candidates = [
            (direction, row + dr, col + dc)
            for direction, (dr, dc) in DELTAS.items()
            if 0 <= row + dr < 11 and 0 <= col + dc < 11
            and grid[row + dr][col + dc] in (0, 97, 98, 99)
        ]
        self.assertTrue(candidates, "floor-00 source spawn has no walkable neighbor")
        direction, next_row, next_col = candidates[0]
        result = json.loads(run({"keys": keys, "arrow_ids": [direction]}))
        self.assertEqual(result["initial_state"], initial)
        self.assertEqual(len(result["frames"]), 1)
        self.assertEqual(result["frames"][0]["arrow_id"], direction)
        self.assertEqual(result["frames"][0]["event"], "move")
        self.assertEqual((result["final_state"]["row"], result["final_state"]["col"]),
                         (next_row, next_col))
        self.assertEqual(result["frames"][0]["state"], result["final_state"])

    def test_invalid_nonempty_direction_fails_closed(self):
        with self.assertRaises(ValueError):
            run({"keys": {"yellow": 0, "blue": 0, "red": 0}, "arrow_ids": [0]})


if __name__ == "__main__":
    unittest.main()
