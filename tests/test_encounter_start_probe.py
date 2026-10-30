"""Cross-runtime vectors derived from the original Move_arrow encounter branch."""
import json
import unittest
from pathlib import Path
from core.encounter_start_probe import start_encounter

CASES=json.loads((Path(__file__).parent/'fixtures'/'encounter_start_cases.json').read_text(encoding='utf-8'))


def make_world(case):
    grid=[[0]*11 for _ in range(11)]
    grid[5][6]=case['tile']
    return {'grid':grid,'row':5,'col':5,**case['hero'],'display_kill':0,'key_flag':1}


class EncounterStartTests(unittest.TestCase):
    def test_original_vectors(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                world=make_world(case)
                original=json.dumps(world,sort_keys=True)
                result=start_encounter(world,2,{str(case['enemy_id']):case['monster']})
                self.assertEqual(result['event'],case['event'])
                self.assertEqual(result['state']['hp'],case['hp_after'])
                self.assertEqual(result['sound'],case['sound'])
                self.assertEqual(result['preview']['enemy_id'],case['enemy_id'])
                self.assertEqual(result['state'].get('boss_kills'),case.get('boss_kills'))
                self.assertEqual(result['state']['grid'][5][6],case['tile'])
                self.assertEqual([result['state']['row'],result['state']['col']],[5,5])
                if result['event']=='encounter_started':
                    self.assertEqual(result['state']['display_kill'],1)
                    self.assertEqual(result['state']['key_flag'],0)
                    self.assertEqual([result['state']['boss_row'],result['state']['boss_col']],[5,6])
                    self.assertEqual(result['battle']['right_hp'],case['hp_after'])
                    self.assertEqual(result['battle']['life'],case['hero']['life'])
                else:
                    self.assertIsNone(result['battle'])
                    self.assertEqual(result['state']['display_kill'],0)
                self.assertEqual(json.dumps(world,sort_keys=True),original)

    def test_rejects_unverified_or_invalid_target(self):
        world=make_world(CASES[0]);world['grid'][5][6]=13
        with self.assertRaisesRegex(ValueError,'not an original monster'):
            start_encounter(world,2,{})
        world=make_world(CASES[0])
        with self.assertRaisesRegex(ValueError,'missing verified monster'):
            start_encounter(world,2,{})
        with self.assertRaisesRegex(ValueError,'outside floor'):
            start_encounter({**world,'col':10},2,{})


if __name__=='__main__':unittest.main()
