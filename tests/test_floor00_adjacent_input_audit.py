"""Floor-00 source-pinned adjacent-input audit, with no skipped directions.

This checks probe classification only, not original Flash runtime parity.
"""
import json
import unittest

from core.movement_probe import DELTAS, UnsupportedTileError
from tools.floor00_trace_cli import run


class Floor00AdjacentInputAuditTests(unittest.TestCase):
    def test_all_four_spawn_directions_are_accounted_for(self):
        keys = {"yellow": 0, "blue": 0, "red": 0}
        initial = json.loads(run({"keys": keys, "arrow_ids": []}))["initial_state"]
        row, col, grid = initial["row"], initial["col"], initial["grid"]
        checked = 0
        for direction, (dr, dc) in DELTAS.items():
            nr, nc = row + dr, col + dc
            if not (0 <= nr < 11 and 0 <= nc < 11):
                expected = "boundary"
            else:
                tile = grid[nr][nc]
                if tile == 1:
                    expected = "wall"
                elif tile in (0, 97, 98, 99):
                    expected = "move"
                elif tile in (2, 3, 4):
                    expected = {2: "yellow", 3: "blue", 4: "red"}[tile]
                    expected = "locked_" + expected + "_door"
                elif tile in (6, 7, 8):
                    expected = "pickup_" + {6: "yellow", 7: "blue", 8: "red"}[tile] + "_key"
                elif tile in (9, 10, 11, 12):
                    expected = "missing_stat"
                else:
                    expected = None
            with self.subTest(direction=direction, expected=expected):
                if expected == "missing_stat":
                    with self.assertRaisesRegex(ValueError, "hero stat"):
                        run({"keys": keys, "arrow_ids": [direction]})
                elif expected is None:
                    with self.assertRaises(UnsupportedTileError):
                        run({"keys": keys, "arrow_ids": [direction]})
                else:
                    result = json.loads(run({"keys": keys, "arrow_ids": [direction]}))
                    self.assertEqual(result["frames"][0]["event"], expected)
                    self.assertEqual(result["initial_state"], initial)
                    self.assertEqual(len(result["frames"]), 1)
            checked += 1
        self.assertEqual(checked, 4)


if __name__ == "__main__":
    unittest.main()
