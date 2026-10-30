"""Original button-handler and cross-runtime arrow-turn vectors."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from core.arrow_turn_probe import classify_arrow_input, step_arrow_turn, replay_arrow_turns
from core.movement_probe import DELTAS

CASES = json.loads((Path(__file__).parent / "fixtures" / "arrow_turn_cases.json").read_text(encoding="utf-8"))
MONSTERS = {"0": [50, 20, 1, 1, 1, "绿头怪"]}

def world_for(case):
    grid = [[0] * 11 for _ in range(11)]
    dr, dc = DELTAS[case["arrow"]]
    grid[5 + dr][5 + dc] = case["tile"]
    world = {"grid": grid, "row": 5, "col": 5, "hp": 100, "attack": 51,
             "defense": 10, "life": 0, "line": 1, "money": 0, "mp": 0,
             "keys": {"yellow": 0, "blue": 0, "red": 0},
             "key_flag": 1, "display_list": 0, "display_jump": 0,
             "display_text": 0, "display_buy": 0, "display_kill": 0}
    world.update(case.get("hero", {}))
    world.update(case.get("flags", {}))
    world["keys"].update(case.get("keys", {}))
    return world

class ArrowTurnTests(unittest.TestCase):
    def test_original_button_and_turn_vectors(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                world = world_for(case)
                before = deepcopy(world)
                if "error" in case:
                    with self.assertRaisesRegex(ValueError, case["error"]):
                        step_arrow_turn(world, case["arrow"], MONSTERS, case.get("rolls", []))
                else:
                    result = step_arrow_turn(world, case["arrow"], MONSTERS, case.get("rolls", []))
                    state, expected = result["state"], case["expected"]
                    self.assertEqual(result["event"], expected["event"])
                    self.assertEqual([state["row"], state["col"]], expected["position"])
                    for key in ("key_flag", "display_text", "open_room", "hp", "attack", "money", "mp"):
                        if key in expected:
                            self.assertEqual(state[key], expected[key])
                    if "yellow" in expected:
                        self.assertEqual(state["keys"]["yellow"], expected["yellow"])
                    if "target_tile" in expected:
                        dr, dc = DELTAS[case["arrow"]]
                        self.assertEqual(state["grid"][5 + dr][5 + dc], expected["target_tile"])
                    if "rolls_used" in expected:
                        self.assertEqual(result["rolls_used"], expected["rolls_used"])
                self.assertEqual(world, before)

    def test_replay_never_autocloses_text_or_door(self):
        pickup = world_for(CASES[2])
        result = replay_arrow_turns(pickup, [{"arrow_id": 2}, {"arrow_id": 2}], MONSTERS)
        self.assertEqual([t["event"] for t in result["trace"]], ["pickup_yellow_key", "input_blocked"])
        self.assertEqual(result["state"]["row"], 5)
        self.assertEqual(result["state"]["keys"]["yellow"], 1)
        self.assertEqual(pickup["grid"][5][6], 6)
        door = world_for(CASES[3])
        result = replay_arrow_turns(door, [{"arrow_id": 2}, {"arrow_id": 2}], MONSTERS)
        self.assertEqual([t["event"] for t in result["trace"]], ["open_yellow_door", "input_blocked"])
        self.assertEqual(result["state"]["open_room"], 1)
        self.assertEqual([result["state"]["last_x"], result["state"]["last_y"]], [5, 6])

    def test_pure_walk_replay_and_gate_validation(self):
        walk = world_for(CASES[0])
        result = replay_arrow_turns(walk, [{"arrow_id": 2}, {"arrow_id": 2}], MONSTERS)
        self.assertEqual([t["event"] for t in result["trace"]], ["move", "move"])
        self.assertEqual([result["state"]["row"], result["state"]["col"]], [5, 7])
        self.assertEqual([walk["row"], walk["col"]], [5, 5])
        with self.assertRaisesRegex(ValueError, "flags"):
            classify_arrow_input({"key_flag": 1}, 2)
        with self.assertRaisesRegex(ValueError, "arrow_id"):
            classify_arrow_input(walk, 5)

if __name__ == "__main__":
    unittest.main()
