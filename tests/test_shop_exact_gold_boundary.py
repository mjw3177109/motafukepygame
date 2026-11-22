"""Boundary-value regression for source-scoped shop probes, not Flash runtime parity."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from core.shop_transition_probe import step_shop

ROOT = Path(__file__).resolve().parents[1]
RULES = (
    (2, 1, 25, "hp", 800),
    (2, 2, 25, "attack", 4),
    (2, 3, 25, "defense", 4),
    (4, 1, 10, "yellow_key", 1),
    (4, 2, 50, "blue_key", 1),
    (4, 3, 100, "red_key", 1),
)
JS = """
import {stepShop} from './web/shop_transition_probe.mjs';
const state = JSON.parse(process.argv[1]);
const result = stepShop(state, Number(process.argv[2]), Number(process.argv[3]));
console.log(JSON.stringify({result, original:state}));
"""


class ShopExactGoldBoundaryTest(unittest.TestCase):
    def test_node_required_for_cross_runtime_gate(self):
        self.assertIsNotNone(shutil.which("node"), "Node.js is required; do not silently skip parity")

    def test_exact_cost_and_one_below_for_every_original_rule(self):
        if not shutil.which("node"):
            self.fail("Node.js is required for cross-runtime boundary verification")
        for frame, option, cost, field, delta in RULES:
            for gold in (cost - 1, cost):
                with self.subTest(frame=frame, option=option, gold=gold):
                    state = dict(gold=gold, hp=100, attack=10, defense=10,
                                 yellow_key=0, blue_key=0, red_key=0)
                    original = state.copy()
                    py = step_shop(state, frame, option)
                    completed = subprocess.run(
                        ["node", "--input-type=module", "-e", JS,
                         json.dumps(state), str(frame), str(option)],
                        cwd=ROOT, capture_output=True, text=True, check=True, timeout=15)
                    js = json.loads(completed.stdout)
                    self.assertEqual(py, js["result"])
                    self.assertEqual(js["original"], original)
                    self.assertEqual(state, original)
                    expected_success = gold == cost
                    self.assertEqual(py["success"], expected_success)
                    self.assertEqual(py["state"]["gold"], 0 if expected_success else gold)
                    self.assertEqual(py["state"][field],
                                     original[field] + (delta if expected_success else 0))
                    self.assertEqual(py["sound"], "music_11" if expected_success else "music_09")
                    self.assertEqual(py["provenance"],
                                     "static_actionscript_expectation_not_runtime")


if __name__ == "__main__":
    unittest.main()
