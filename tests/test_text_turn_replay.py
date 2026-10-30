"""Shared fixture tests: real arrow and text probes, no synthetic frame clock."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from core.text_turn_replay import replay_text_turns

CASES = json.loads((Path(__file__).parent/'fixtures'/'text_turn_replay_cases.json').read_text())

def world_for(case):
    grid = [[0]*11 for _ in range(11)]
    grid[5][6] = case['tile']
    world = dict(grid=grid,row=5,col=5,hp=100,attack=51,defense=10,life=0,line=1,
                 money=0,mp=0,keys={'yellow':0,'blue':0,'red':0},
                 key_flag=1,display_list=0,display_jump=0,display_text=0,
                 display_buy=0,display_kill=0,boss_kills=0,floor26_cell_3_5=188)
    world.update(case.get('flags', {}))
    if case.get('omit_floor26_cell'):
        world.pop('floor26_cell_3_5')
    return world

class TextTurnReplayTests(unittest.TestCase):
    def test_shared_vectors(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                world=world_for(case)
                before=deepcopy(world)
                if 'error' in case:
                    with self.assertRaisesRegex(ValueError,case['error']):
                        replay_text_turns(world,case['actions'],{})
                else:
                    result=replay_text_turns(world,case['actions'],{})
                    self.assertEqual([x['event'] for x in result['trace']],case['events'])
                    self.assertEqual([result['state']['row'],result['state']['col']],case['position'])
                    for k in ('key_flag','display_text','game_over_requested'):
                        self.assertEqual(result[k] if k=='game_over_requested' else result['state'][k],case[k])
                    self.assertEqual(result['state']['keys']['yellow'],case['yellow'])
                    if result['game_over_requested']:
                        self.assertIn('goto_game_over',result['trace'][-1]['effects'])
                self.assertEqual(world,before)

if __name__=='__main__': unittest.main()
