import json
import unittest
from pathlib import Path
from core.battle_frame_probe import begin_battle, step_battle_frame

CASES = json.loads((Path(__file__).parent / 'fixtures/battle_frame_probe_cases.json').read_text(encoding='utf-8'))


class BattleFrameProbeTests(unittest.TestCase):
    def test_original_frame_1_damage_order(self):
        monster = [10, 20, 1, 1, 1, '绿头怪']
        hero = {'hp': 5, 'attack': 11, 'defense': 10}
        self.assertEqual(begin_battle(monster, hero, 0), CASES[0]['state'])

    def test_original_frame_24_vectors(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                snapshot = case['state']
                self.assertEqual(step_battle_frame(snapshot, case['roll']), case['expected'])
                self.assertEqual(snapshot, case['state'], 'input snapshot mutated')

    def test_random_roll_is_required_only_for_hero(self):
        with self.assertRaises(ValueError):
            step_battle_frame(CASES[0]['state'])
        with self.assertRaises(ValueError):
            step_battle_frame(CASES[0]['state'], 200)
        with self.assertRaises(ValueError):
            step_battle_frame(CASES[1]['state'], 0)

    def test_bad_state_rejected(self):
        with self.assertRaises(ValueError):
            step_battle_frame({'left_hp': 10})
        with self.assertRaises(ValueError):
            begin_battle([10, 20], {'hp': 5, 'attack': 11, 'defense': 10}, 0)


if __name__ == '__main__':
    unittest.main()
