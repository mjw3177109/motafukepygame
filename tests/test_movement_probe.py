"""Python half of cross-runtime deterministic movement vectors."""
import json
import unittest
from pathlib import Path

from core.movement_probe import UnsupportedTileError, step_move_arrow, DELTAS

CASES = json.loads((Path(__file__).parent / 'fixtures' / 'movement_probe_cases.json').read_text(encoding='utf-8'))


def make_state(case):
    row,col=case.get('start',[5,5])
    grid=[[0]*11 for _ in range(11)]
    dr,dc=DELTAS[case['arrow']]
    nr,nc=row+dr,col+dc
    if 0 <= nr < 11 and 0 <= nc < 11:
        grid[nr][nc]=case['tile']
    if 'origin_tile' in case:
        grid[row][col]=case['origin_tile']
    keys={'yellow':0,'blue':0,'red':0}
    keys.update(case.get('keys',{}))
    return {'grid':grid,'row':row,'col':col,'hp':1000,'attack':10,'defense':10,'keys':keys}


class MovementProbeTests(unittest.TestCase):
    def test_vectors(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                state=make_state(case)
                original=json.dumps(state,sort_keys=True)
                if case.get('error'):
                    with self.assertRaises(UnsupportedTileError):
                        step_move_arrow(state,case['arrow'])
                    continue
                result=step_move_arrow(state,case['arrow'])
                self.assertEqual(result['event'],case['event'])
                out=result['state']
                self.assertEqual([out['row'],out['col']],case['position'])
                for key,amount in case.get('key_delta',{}).items():
                    self.assertEqual(out['keys'][key],state['keys'][key]+amount)
                for stat,amount in case.get('stat_delta',{}).items():
                    self.assertEqual(out[stat],state[stat]+amount)
                if case.get('cleared'):
                    dr,dc=DELTAS[case['arrow']]
                    self.assertEqual(out['grid'][state['row']+dr][state['col']+dc],0)
                if 'origin_after' in case:
                    self.assertEqual(out['grid'][state['row']][state['col']],case['origin_after'])
                if 'target_after' in case:
                    dr,dc=DELTAS[case['arrow']]
                    self.assertEqual(out['grid'][state['row']+dr][state['col']+dc],case['target_after'])
                self.assertEqual(json.dumps(state,sort_keys=True),original)

    def test_reject_non_original_grid(self):
        state=make_state(CASES[0])
        state['grid'].pop()
        with self.assertRaisesRegex(ValueError,'11x11'):
            step_move_arrow(state,1)

    def test_reject_bad_direction(self):
        with self.assertRaisesRegex(ValueError,'arrow_id'):
            step_move_arrow(make_state(CASES[0]),5)


if __name__=='__main__':
    unittest.main()
