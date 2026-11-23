"""Six shop purchase boundaries in Python and JavaScript (static AS only)."""
import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from core.shop_transition_probe import MAX_SAFE_INTEGER, TRANSACTIONS, step_shop

ROOT = Path(__file__).resolve().parents[1]
NODE_SCRIPT = """
import {readFileSync} from 'node:fs';
import {stepShop} from './web/shop_transition_probe.mjs';
const vectors = JSON.parse(readFileSync(0, 'utf8'));
const output = vectors.map(({state, frame, option}) => {
  const before = structuredClone(state);
  let result;
  try { result = {ok:true, value:stepShop(state, frame, option)}; }
  catch { result = {ok:false}; }
  if (JSON.stringify(state) !== JSON.stringify(before)) throw new Error('input mutated');
  return result;
});
process.stdout.write(JSON.stringify(output));
"""

class ShopOverflowBoundaryTests(unittest.TestCase):
    def test_every_purchase_stat_boundary(self):
        self.assertIsNotNone(shutil.which('node'), 'Node.js required; never skip parity')
        base = {'gold': 100, 'hp': 10, 'attack': 3, 'defense': 2,
                'yellow_key': 0, 'blue_key': 0, 'red_key': 0}
        vectors = []
        for (frame, option), (cost, field, delta) in sorted(TRANSACTIONS.items()):
            for overflow in (False, True):
                state = dict(base, gold=cost)
                state[field] = MAX_SAFE_INTEGER - delta + int(overflow)
                vectors.append({'state': state, 'frame': frame, 'option': option,
                                'field': field, 'overflow': overflow})
        payload = [{k: v for k, v in case.items() if k in ('state', 'frame', 'option')}
                   for case in vectors]
        proc = subprocess.run(['node', '--input-type=module', '-e', NODE_SCRIPT],
                              input=json.dumps(payload), text=True, capture_output=True,
                              cwd=ROOT, timeout=20, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        results = json.loads(proc.stdout)
        self.assertEqual(len(results), 12)
        for case, js in zip(vectors, results):
            with self.subTest(frame=case['frame'], option=case['option'],
                              overflow=case['overflow']):
                before = copy.deepcopy(case['state'])
                try:
                    py = {'ok': True, 'value': step_shop(case['state'], case['frame'], case['option'])}
                except ValueError:
                    py = {'ok': False}
                self.assertEqual(case['state'], before)
                self.assertEqual(js, py)
                if case['overflow']:
                    self.assertFalse(py['ok'], 'Overflow must be rejected')
                else:
                    self.assertTrue(py['ok'], 'Exact safe-integer boundary must succeed')
                    self.assertTrue(py['value']['success'])
                    self.assertEqual(py['value']['state'][case['field']], MAX_SAFE_INTEGER)
                    self.assertEqual(py['value']['state']['gold'], 0)

if __name__ == '__main__':
    unittest.main()
