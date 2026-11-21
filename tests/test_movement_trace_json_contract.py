"""JSON interchange contract for the verified movement probe subset.

These tests do not establish original Flash parity or playable runtime support.
"""
import json
import unittest
from copy import deepcopy

from core.movement_trace import trace_move_arrows


def fixture():
    grid = [[0 for _ in range(11)] for _ in range(11)]
    grid[5][5] = 99
    grid[5][6] = 6
    grid[5][7] = 2
    return {
        "grid": grid, "row": 5, "col": 5,
        "keys": {"yellow": 0, "blue": 0, "red": 0},
    }


class MovementTraceJsonContractTests(unittest.TestCase):
    def test_round_trip_preserves_events_and_states(self):
        initial = fixture()
        original = deepcopy(initial)
        result = trace_move_arrows(initial, [2, 2, 2, 2])
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True)
        decoded = json.loads(encoded)
        self.assertEqual(decoded, result)
        self.assertEqual([frame["event"] for frame in decoded["frames"]],
                         ["pickup_yellow_key", "move", "open_yellow_door", "move"])
        self.assertEqual(decoded["final_state"]["keys"]["yellow"], 0)
        self.assertEqual(decoded["final_state"]["col"], 7)
        self.assertEqual(initial, original)

    def test_json_bytes_are_deterministic(self):
        first = json.dumps(trace_move_arrows(fixture(), [2, 2, 2]),
                           sort_keys=True, separators=(",", ":"), allow_nan=False)
        second = json.dumps(trace_move_arrows(fixture(), [2, 2, 2]),
                            sort_keys=True, separators=(",", ":"), allow_nan=False)
        self.assertEqual(first.encode("utf-8"), second.encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
