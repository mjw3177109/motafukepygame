"""Frame34 loop decisions checked against FFDec sprite 453 ActionScript."""
import json
import unittest
from copy import deepcopy
from pathlib import Path

from core.battle_frame_probe import begin_battle
from core.battle_timeline_probe import replay_to_victory
from core.encounter_start_probe import start_encounter
from core.battle_settlement_probe import frame54_handoff, consume_battle_completion

CASES = json.loads((Path(__file__).parent / "fixtures" / "battle_timeline_cases.json").read_text(encoding="utf-8"))


class BattleTimelineTests(unittest.TestCase):
    def test_shared_original_branch_vectors(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                initial = begin_battle(case["monster"], case["hero"], case["life"])
                before = deepcopy(initial)
                result = replay_to_victory(initial, case["rolls"])
                exp = case["expected"]
                self.assertEqual(result["next_frame"], 35)
                self.assertEqual(result["rolls_used"], exp["rolls_used"])
                self.assertEqual(len(result["steps"]), exp["actions"])
                self.assertEqual(sum(x["event"] == "monster_counterattack" for x in result["steps"]), exp["counterattacks"])
                self.assertEqual(result["battle"]["left_hp"], exp["left_hp"])
                self.assertEqual(result["battle"]["right_hp"], exp["right_hp"])
                self.assertEqual(result["battle"]["kill_number"], exp["kill_number"])
                self.assertEqual([x["transition"] for x in result["steps"]], exp["transitions"])
                self.assertEqual(initial, before)

    def test_fails_closed_on_missing_extra_rolls_or_infinite_loop(self):
        case = CASES[0]
        battle = begin_battle(case["monster"], case["hero"], case["life"])
        with self.assertRaisesRegex(ValueError, "missing"):
            replay_to_victory(battle, [])
        with self.assertRaisesRegex(ValueError, "unused"):
            replay_to_victory(battle, [199, 199])
        with self.assertRaisesRegex(ValueError, "positive"):
            replay_to_victory({**battle, "kill_right": 0}, [199])
        longer = CASES[1]
        longer_battle = begin_battle(longer["monster"], longer["hero"], longer["life"])
        with self.assertRaisesRegex(ValueError, "max_actions"):
            replay_to_victory(longer_battle, longer["rolls"], 1)

    def test_encounter_through_reward_without_phantom_retaliation(self):
        monster = CASES[0]["monster"]
        grid = [[0] * 11 for _ in range(11)]
        grid[5][6] = 40
        world = {"grid": grid, "row": 5, "col": 5, "hp": 100,
                 "attack": 11, "defense": 10, "life": 0, "line": 1,
                 "display_kill": 0, "key_flag": 1, "money": 0, "mp": 0}
        before = deepcopy(world)
        started = start_encounter(world, 2, {"0": monster})
        self.assertEqual(started["event"], "encounter_started")
        replay = replay_to_victory(started["battle"], [199])
        self.assertEqual(len(replay["steps"]), 1)
        handoff = frame54_handoff(started["state"], replay["battle"])
        reward = consume_battle_completion(handoff["state"], monster)
        self.assertEqual((reward["state"]["hp"], reward["state"]["money"], reward["state"]["mp"]), (100, 1, 1))
        self.assertEqual(reward["state"]["grid"][5][6], 0)
        self.assertEqual(reward["state"]["display_kill"], 0)
        self.assertEqual(world, before)


if __name__ == "__main__":
    unittest.main()
