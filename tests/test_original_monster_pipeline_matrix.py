"""Source-roster deterministic full battle pipeline matrix (synthetic hero inputs).

Original monster rows are audited elsewhere against game.swf/FFDec. These
are NOT Flash player recordings or proof of original gameplay parity.
"""
import json
import unittest
from copy import deepcopy
from pathlib import Path

from core.encounter_pipeline_probe import resolve_encounter

ROOT = Path(__file__).resolve().parents[1]
ROSTER = json.loads((ROOT / "data/original_combat_tables.json").read_text(encoding="utf-8"))
SPECIAL = {20: 100, 12: 300, 10: 250000, 17: 333333}


def make_world(enemy_id, monster, two_hit):
    grid = [[0] * 11 for _ in range(11)]
    for row in range(3, 6):
        for col in range(5, 8):
            grid[row][col] = 7
    grid[0][0] = 17  # Sentinel outside either clearance footprint.
    grid[5][6] = enemy_id + 40 if enemy_id < 31 else (188 if enemy_id == 31 else 198)
    return {
        "grid": grid, "row": 5, "col": 5, "hp": 1000000,
        "attack": monster[2] + monster[0] - int(two_hit),
        "defense": monster[1] - (7 if two_hit else 0),
        "life": 0, "line": 1, "display_kill": 0, "key_flag": 1,
        "money": 11, "mp": 13,
    }


class OriginalMonsterFullPipelineMatrixTests(unittest.TestCase):
    def test_all_33_monsters_one_and_two_hit_settlement(self):
        self.assertEqual(set(ROSTER["monsters"]), {str(i) for i in range(33)})
        self.assertFalse(ROSTER["gameplay_parity_verified"])
        self.assertFalse(ROSTER["gymnasium_ready"])
        for enemy_id in range(33):
            monster = ROSTER["monsters"][str(enemy_id)]
            for two_hit in (False, True):
                with self.subTest(monster=enemy_id, two_hit=two_hit):
                    world = make_world(enemy_id, monster, two_hit)
                    original = deepcopy(world)
                    rolls = [199, 199] if two_hit else [199]
                    result = resolve_encounter(world, 2, {str(enemy_id): monster}, rolls)
                    expected_hp = 1000000 - SPECIAL.get(enemy_id, 0) - (7 if two_hit else 0)
                    expected_cleared = (
                        [[r, c] for r in range(3, 6) for c in range(5, 8)]
                        if enemy_id in (31, 32) else [[5, 6]]
                    )
                    self.assertEqual(world, original, "input world mutated")
                    self.assertEqual(result["cleared"], expected_cleared)
                    self.assertEqual(result["state"]["hp"], expected_hp)
                    self.assertEqual(result["battle"]["right_hp"], expected_hp)
                    self.assertEqual(result["battle"]["left_hp"], 0)
                    self.assertEqual(result["state"]["money"], 11 + monster[3])
                    self.assertEqual(result["state"]["mp"], 13 + monster[4])
                    self.assertEqual(result["state"]["display_kill"], 0)
                    self.assertEqual(result["state"]["grid"][0][0], 17)
                    self.assertEqual(result["state"]["grid"][3][5], 0 if enemy_id in (31, 32) else 7)
                    self.assertEqual(result["state"]["grid"][5][6], 0)
                    self.assertEqual(len(result["steps"]), 3 if two_hit else 1)
                    self.assertEqual(
                        sum(s["event"] == "monster_counterattack" for s in result["steps"]),
                        1 if two_hit else 0,
                    )
                    self.assertEqual(
                        [e["event"] for e in result["events"]],
                        ["encounter_started", "frame35_reached", "frame54_handoff", "battle_reward"],
                    )
                    self.assertEqual(result["state"].get("boss_kills"), 1 if enemy_id == 19 else None)


    def test_all_33_monsters_critical_zero_vs_noncritical_one(self):
        """Flash random(200) roll 0 crits at life=0; roll 1 does not."""
        for enemy_id in range(33):
            monster = ROSTER["monsters"][str(enemy_id)]
            half_hit = (monster[0] + 1) // 2
            for roll in (0, 1):
                with self.subTest(monster=enemy_id, roll=roll):
                    world = make_world(enemy_id, monster, False)
                    world["attack"] = monster[2] + half_hit
                    world["defense"] = monster[1] - 7
                    before = deepcopy(world)
                    result = resolve_encounter(world, 2, {str(enemy_id): monster},
                                               [roll] if roll == 0 else [roll, roll])
                    hero_steps = [s for s in result["steps"] if s["event"] == "hero_attack"]
                    self.assertEqual([s["critical"] for s in hero_steps],
                                     [True] if roll == 0 else [False, False])
                    self.assertEqual(hero_steps[0]["damage"], half_hit * (2 if roll == 0 else 1))
                    self.assertEqual(len(result["steps"]), 1 if roll == 0 else 3)
                    self.assertEqual(result["state"]["hp"],
                                     1000000 - SPECIAL.get(enemy_id, 0) - (0 if roll == 0 else 7))
                    self.assertEqual(result["state"]["money"], 11 + monster[3])
                    self.assertEqual(result["state"]["mp"], 13 + monster[4])
                    self.assertEqual(result["battle"]["left_hp"], 0)
                    self.assertEqual(result["state"]["grid"][5][6], 0)
                    self.assertEqual(world, before)

if __name__ == "__main__":
    unittest.main()
