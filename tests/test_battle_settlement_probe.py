import json
import unittest
from copy import deepcopy
from pathlib import Path
from core.battle_settlement_probe import frame54_handoff, consume_battle_completion

CASES = json.loads((Path(__file__).parent / 'fixtures/battle_settlement_cases.json').read_text(encoding='utf-8'))


class SettlementTests(unittest.TestCase):
    def test_shared_cases(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                before = deepcopy(case['world'])
                handoff = frame54_handoff(before, case['battle'])
                self.assertEqual(handoff, case['handoff'])
                self.assertEqual(consume_battle_completion(handoff['state'], case['monster']), case['settled'])
                self.assertEqual(before, case['world'])

    def test_rejects_early_and_duplicate_settlement(self):
        case = CASES[0]
        with self.assertRaisesRegex(ValueError, 'display_kill=2'):
            consume_battle_completion(case['world'], case['monster'])
        with self.assertRaisesRegex(ValueError, 'display_kill=2'):
            consume_battle_completion(case['settled']['state'], case['monster'])

    def test_rejects_out_of_bounds_boss(self):
        case = deepcopy(CASES[1])
        case['handoff']['state']['boss_row'] = 1
        with self.assertRaisesRegex(ValueError, 'footprint'):
            consume_battle_completion(case['handoff']['state'], case['monster'])

    def test_frame54_requires_monster_dead(self):
        case = CASES[0]
        with self.assertRaisesRegex(ValueError, 'completed monster'):
            frame54_handoff(case['world'], {'left_hp':1,'right_hp':5})



    def test_zero_or_negative_hp_source_scoped_reward_chain(self):
        """Synthetic frame54 -> sprite855 -> Move_arrow(100), not Flash death parity."""
        case = CASES[0]
        for hp in (0, -15):
            with self.subTest(hp=hp):
                world = deepcopy(case['world'])
                battle = {**case['battle'], 'right_hp': hp}
                handoff = frame54_handoff(world, battle)
                reward = consume_battle_completion(handoff['state'], case['monster'])
                self.assertEqual(reward['state']['hp'], hp)
                self.assertEqual(reward['state']['money'], world['money'] + case['monster'][3])
                self.assertEqual(reward['state']['mp'], world['mp'] + case['monster'][4])
                self.assertEqual(reward['state']['grid'][5][5], 0)
                self.assertEqual(world, case['world'])

if __name__ == '__main__':
    unittest.main()
