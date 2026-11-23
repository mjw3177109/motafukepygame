"""Guard cross-runtime rejection parity for static ActionScript shop probes.

This is not a Flash runtime or UI parity test.
"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from core.shop_transition_probe import step_shop

ROOT = Path(__file__).resolve().parents[1]
NODE = """
import {stepShop} from './web/shop_transition_probe.mjs';
const state = JSON.parse(process.argv[1]);
const frame = JSON.parse(process.argv[2]);
const option = JSON.parse(process.argv[3]);
try {
  stepShop(state, frame, option);
  console.log(JSON.stringify({accepted:true}));
} catch (error) {
  console.log(JSON.stringify({accepted:false}));
}
"""
BASE = dict(gold=100, hp=100, attack=10, defense=10,
            yellow_key=0, blue_key=0, red_key=0)


@unittest.skipUnless(shutil.which("node"), "Node.js required for cross-runtime parity")
class ShopCrossRuntimeRejectionTest(unittest.TestCase):
    def test_invalid_inputs_rejected_in_both_runtimes(self):
        cases = [
            ("negative gold", {**BASE, "gold": -1}, 2, 1),
            ("fractional hp", {**BASE, "hp": 1.5}, 2, 1),
            ("missing key", {k: v for k, v in BASE.items() if k != "red_key"}, 4, 1),
            ("unsafe integer", {**BASE, "attack": 9007199254740992}, 2, 2),
            ("boolean field", {**BASE, "gold": True}, 2, 1),
            ("invalid frame", BASE, 3, 1),
            ("invalid option", BASE, 2, 5),
            ("boolean frame", BASE, True, 1),
            ("boolean option", BASE, 2, True),
            ("overflow", {**BASE, "hp": 9007199254740991}, 2, 1),
        ]
        for label, state, frame, option in cases:
            with self.subTest(case=label):
                with self.assertRaises(ValueError):
                    step_shop(state, frame, option)
                completed = subprocess.run(
                    ["node", "--input-type=module", "-e", NODE,
                     json.dumps(state), json.dumps(frame), json.dumps(option)],
                    cwd=ROOT, capture_output=True, text=True, check=True, timeout=15,
                )
                self.assertEqual(json.loads(completed.stdout), {"accepted": False})


if __name__ == "__main__":
    unittest.main()
