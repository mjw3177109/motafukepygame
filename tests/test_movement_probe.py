"""Python half of cross-runtime deterministic movement vectors."""
import json
import unittest
from copy import deepcopy
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

    def test_reject_invalid_non_target_cells_without_mutation(self):
        # A non-target cell must not bypass Python validation when JS rejects it.
        for invalid in (True, 2**53, -(2**53), "0", 0.0):
            with self.subTest(invalid=repr(invalid)):
                state = make_state(CASES[0])
                state["grid"][9][9] = invalid
                before = deepcopy(state)
                with self.assertRaisesRegex(ValueError, "11x11"):
                    step_move_arrow(state, 2)
                self.assertEqual(state, before)

    def test_reject_non_list_grid_and_row(self):
        for kind in ("tuple_grid", "tuple_row", "dict_row"):
            with self.subTest(kind=kind):
                state = make_state(CASES[0])
                if kind == "tuple_grid":
                    state["grid"] = tuple(state["grid"])
                elif kind == "tuple_row":
                    state["grid"][9] = tuple(state["grid"][9])
                else:
                    state["grid"][9] = dict(enumerate(state["grid"][9]))
                before = deepcopy(state)
                with self.assertRaisesRegex(ValueError, "11x11"):
                    step_move_arrow(state, 2)
                self.assertEqual(state, before)


    def test_reject_malformed_key_inventory_without_mutation(self):
        invalid = [
            None, [], {"yellow": 0, "blue": 0},
            {"yellow": True, "blue": 0, "red": 0},
            {"yellow": "1", "blue": 0, "red": 0},
            {"yellow": 2**53, "blue": 0, "red": 0},
        ]
        for keys in invalid:
            with self.subTest(keys=repr(keys)):
                state = make_state(CASES[5])
                state["keys"] = keys
                before = deepcopy(state)
                with self.assertRaisesRegex(ValueError, "key inventory"):
                    step_move_arrow(state, 2)
                self.assertEqual(state, before)

    def test_key_pickup_safe_integer_overflow_fails_closed(self):
        state = make_state(CASES[5])
        state["keys"]["yellow"] = (1 << 53) - 1
        before = deepcopy(state)
        with self.assertRaisesRegex(ValueError, "key inventory overflow"):
            step_move_arrow(state, 2)
        self.assertEqual(state, before)

    def test_reject_bad_direction(self):
        with self.assertRaisesRegex(ValueError,'arrow_id'):
            step_move_arrow(make_state(CASES[0]),5)


if __name__=='__main__':
    unittest.main()
