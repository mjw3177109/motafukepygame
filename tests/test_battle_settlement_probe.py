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

    def test_rejects_boolean_phase_and_monster_death_flags(self):
        """Python bool is an int subclass; JavaScript rejects these phase values."""
        case = CASES[0]
        for phase in (True, False):
            with self.subTest(phase=phase):
                world = {**case['world'], 'display_kill': phase}
                with self.assertRaisesRegex(ValueError, 'active battle'):
                    frame54_handoff(world, case['battle'])
        with self.assertRaisesRegex(ValueError, 'completed monster'):
            frame54_handoff(case['world'], {**case['battle'], 'left_hp': False})
        with self.assertRaisesRegex(ValueError, 'display_kill=2'):
            consume_battle_completion({**case['handoff']['state'], 'display_kill': True}, case['monster'])

    def test_boss32_footprint_at_last_valid_boundary(self):
        """Boss 32 clears exactly nine tiles at the bottom-right valid footprint."""
        case = deepcopy(CASES[1])
        world = case['handoff']['state']
        world['boss_id'] = 32
        world['boss_row'] = 10
        world['boss_col'] = 9
        original = deepcopy(world)
        result = consume_battle_completion(world, case['monster'])
        expected = [[r, c] for r in (8, 9, 10) for c in (8, 9, 10)]
        self.assertEqual(result['cleared'], expected)
        self.assertEqual(result['removed_clips'], [f"mt_m_{r}_{c}" for r, c in expected])
        for r in range(11):
            for c in range(11):
                self.assertEqual(result['state']['grid'][r][c],
                                 0 if [r, c] in expected else original['grid'][r][c])
        self.assertEqual(result['state']['money'], original['money'] + case['monster'][3])
        self.assertEqual(result['state']['mp'], original['mp'] + case['monster'][4])
        self.assertEqual(world, original)

if __name__ == '__main__':
    unittest.main()
