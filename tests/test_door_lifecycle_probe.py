"""Cross-language door lifecycle vectors with original arrow router integration."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from core.door_lifecycle_probe import step_door_lifecycle
from core.arrow_turn_probe import step_arrow_turn

CASES = json.loads((Path(__file__).parent / "fixtures" / "door_lifecycle_cases.json").read_text())


def world_for(case):
    grid = [[0] * 11 for _ in range(11)]
    grid[5][6] = case.get("tile", 0)
    keys = {"yellow": 0, "blue": 0, "red": 0}
    if "key" in case:
        keys[case["key"]] = 1
    return dict(grid=grid, row=5, col=5, hp=100, attack=51, defense=10,
                life=0, line=1, money=0, mp=0, keys=keys, key_flag=1,
                display_list=0, display_jump=0, display_text=0, display_buy=0,
                display_kill=0, open_room=0, last_x=5, last_y=6)


class DoorLifecycleTests(unittest.TestCase):
    def test_shared_sprite_frames_and_cleanup(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                initial = world_for(case)
                if "tile" in case:
                    opened = step_arrow_turn(initial, 2, {})
                    self.assertEqual(opened["event"], "open_" + case["key"] + "_door")
                    self.assertEqual(opened["state"]["keys"][case["key"]], 0)
                    self.assertEqual(opened["state"]["grid"][5][6], 0)
                    self.assertEqual(step_arrow_turn(opened["state"], 2, {})["event"], "input_blocked")
                    before = opened["state"]
                else:
                    before = deepcopy(initial)
                    before.update(open_room=1, key_flag=0)
                preserved = deepcopy(before)
                ready = step_door_lifecycle(before, "frame_complete", sprite=case["sprite"], frame=case["frame"])
                self.assertEqual(ready["state"]["open_room"], 2)
                self.assertEqual(ready["state"]["key_flag"], 0)
                self.assertEqual(before, preserved)
                finished = step_door_lifecycle(ready["state"], "cleanup")
                self.assertEqual(finished["state"]["open_room"], 0)
                self.assertEqual(finished["state"]["key_flag"], 1)
                self.assertEqual(finished["effects"], ["remove_map_sprite:mt_m_5_6"])
                self.assertEqual(ready["state"]["open_room"], 2)
                if "tile" in case:
                    moved = step_arrow_turn(finished["state"], 2, {})
                    self.assertEqual(moved["event"], "move")
                    self.assertEqual((moved["state"]["row"], moved["state"]["col"]), (5, 6))

    def test_fail_closed_invalid_phase_sprite_or_coordinates(self):
        state = world_for(CASES[0])
        with self.assertRaisesRegex(ValueError, "open_room=2"):
            step_door_lifecycle(state, "cleanup")
        state.update(open_room=1, key_flag=0)
        for sprite, frame in [("mt_15", 10), ("mt_02", 5), ("mt_99", 10)]:
            with self.subTest(sprite=sprite, frame=frame):
                with self.assertRaisesRegex(ValueError, "unverified door sprite/frame"):
                    step_door_lifecycle(state, "frame_complete", sprite=sprite, frame=frame)
        ready = step_door_lifecycle(state, "frame_complete", sprite="mt_02", frame=10)["state"]
        with self.assertRaisesRegex(ValueError, "open_room=1"):
            step_door_lifecycle(ready, "frame_complete", sprite="mt_02", frame=10)
        for x in (None, -1, 11, True):
            with self.subTest(x=x):
                with self.assertRaisesRegex(ValueError, "Last_x/Last_y"):
                    step_door_lifecycle(dict(ready, last_x=x), "cleanup")
        with self.assertRaisesRegex(ValueError, "cleanup does not accept"):
            step_door_lifecycle(ready, "cleanup", sprite="mt_02", frame=10)
