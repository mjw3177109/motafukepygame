"""Regression for the strict JSON movement trace CLI contract."""
import json
import unittest

from tools.movement_trace_cli import run
from core.movement_probe import UnsupportedTileError


def state():
    grid = [[0] * 11 for _ in range(11)]
    grid[5][5] = 99
    grid[5][6] = 6
    grid[5][7] = 2
    return {"grid": grid, "row": 5, "col": 5,
            "keys": {"yellow": 0, "blue": 0, "red": 0}}


class TraceCliTests(unittest.TestCase):
    def test_canonical_output_and_round_trip(self):
        request = {"initial_state": state(), "arrow_ids": [2, 2, 2, 2]}
        first = run(request)
        self.assertEqual(first, run(request))
        result = json.loads(first)
        self.assertEqual(result["final_state"]["col"], 7)
        self.assertEqual([f["event"] for f in result["frames"]],
                         ["pickup_yellow_key", "move", "open_yellow_door", "move"])
        self.assertEqual(request["initial_state"]["keys"]["yellow"], 0)

    def test_reject_extra_request_fields(self):
        with self.assertRaises(ValueError):
            run({"initial_state": state(), "arrow_ids": [], "ignored": True})

    def test_fail_closed_on_unimplemented_tile(self):
        initial = state()
        initial["grid"][5][6] = 24
        with self.assertRaises(UnsupportedTileError):
            run({"initial_state": initial, "arrow_ids": [2]})


if __name__ == "__main__":
    unittest.main()
