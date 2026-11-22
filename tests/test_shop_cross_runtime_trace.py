"""Compare Python and JS *static* shop probes, not Flash runtime behavior."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from core.shop_transition_probe import step_shop

ROOT = Path(__file__).resolve().parents[1]
NODE_SCRIPT = r"""
import {stepShop} from './web/shop_transition_probe.mjs';
const steps = JSON.parse(process.argv[1]);
let state = JSON.parse(process.argv[2]);
const output = [];
for (const [frame, option] of steps) {
  const result = stepShop(state, frame, option);
  output.push(result);
  state = result.state;
}
console.log(JSON.stringify(output));
"""


@unittest.skipUnless(shutil.which('node'), 'Node.js required for cross-runtime parity')
class ShopCrossRuntimeTraceTest(unittest.TestCase):
    def test_static_shop_purchase_insufficient_and_exit_traces(self):
        initial = dict(gold=220, hp=100, attack=10, defense=10,
                       yellow_key=0, blue_key=0, red_key=0)
        traces = [
            [(2, 1), (2, 2), (2, 3), (2, 1), (2, 4)],
            [(4, 1), (4, 2), (4, 3), (4, 1), (4, 4)],
            [(2, 4)], [(4, 4)],
        ]
        for steps in traces:
            with self.subTest(steps=steps):
                state = initial.copy()
                expected = []
                for frame, option in steps:
                    result = step_shop(state, frame, option)
                    expected.append(result)
                    state = result['state']
                completed = subprocess.run(
                    ['node', '--input-type=module', '-e', NODE_SCRIPT,
                     json.dumps(steps), json.dumps(initial)],
                    cwd=ROOT, capture_output=True, text=True, check=True,
                    timeout=15,
                )
                self.assertEqual(json.loads(completed.stdout), expected)
                self.assertEqual(initial['gold'], 220)
                self.assertTrue(all(r['provenance'] ==
                    'static_actionscript_expectation_not_runtime' for r in expected))


if __name__ == '__main__':
    unittest.main()
