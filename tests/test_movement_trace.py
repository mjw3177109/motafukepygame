"""Contract tests for deterministic traces, not original Flash parity."""
import unittest
from copy import deepcopy
from core.movement_probe import UnsupportedTileError
from core.movement_trace import trace_move_arrows


def snapshot():
    grid = [[0] * 11 for _ in range(11)]
    grid[5][5] = 99
    grid[5][6] = 1
    grid[4][5] = 6
    return {"grid": grid, "row": 5, "col": 5,
            "keys": {"yellow": 0, "blue": 0, "red": 0}}


class MovementTraceTests(unittest.TestCase):
    def test_determinism_and_immutable_input(self):
        initial = snapshot()
        before = deepcopy(initial)
        first = trace_move_arrows(initial, [2, 3, 3])
        self.assertEqual(first, trace_move_arrows(initial, [2, 3, 3]))
        self.assertEqual(initial, before)
        self.assertEqual([f["event"] for f in first["frames"]],
                         ["wall", "pickup_yellow_key", "move"])
        self.assertEqual(first["final_state"]["keys"]["yellow"], 1)
        self.assertEqual((first["final_state"]["row"], first["final_state"]["col"]), (4, 5))
        self.assertEqual(first["frames"][0]["state"]["row"], 5)
        self.assertEqual(first["frames"][1]["state"]["row"], 5)

    def test_empty_sequence(self):
        initial = snapshot()
        result = trace_move_arrows(initial, [])
        self.assertEqual(result["frames"], [])
        self.assertEqual(result["final_state"], initial)

    def test_unsupported_tile_fails_closed(self):
        initial = snapshot()
        initial["grid"][5][6] = 24
        with self.assertRaises(UnsupportedTileError):
            trace_move_arrows(initial, [2])

    def test_invalid_input_fails_closed(self):
        with self.assertRaises(ValueError):
            trace_move_arrows(snapshot(), [0])
        with self.assertRaises(ValueError):
            trace_move_arrows(snapshot(), (1,))


if __name__ == "__main__":
    unittest.main()
