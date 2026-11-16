"""Cross-language shop transition parity; static ActionScript scope only.

Runs both pure probes on identical source-derived vectors. This is NOT
Flash runtime, UI, or full-game parity evidence.
"""
import copy
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from core.shop_transition_probe import MAX_SAFE_INTEGER, step_shop
from tools.shop_trace_cases import build_cases

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/original_shop_transactions_static.json"
NODE_SCRIPT = """
import {readFileSync} from 'node:fs';
import {stepShop} from './web/shop_transition_probe.mjs';
const vectors = JSON.parse(readFileSync(0, 'utf8'));
const output = vectors.map(({state, frame, option}) => {
  try { return {ok:true, value:stepShop(state, frame, option)}; }
  catch (err) { return {ok:false}; }
});
process.stdout.write(JSON.stringify(output));
"""


class ShopCrossLanguageParityTests(unittest.TestCase):
    def test_source_vectors_and_rejections(self):
        self.assertIsNotNone(shutil.which("node"), "Node.js is required for cross-language parity; do not silently skip")
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(fixture["verification"], "static_actionscript_only_not_runtime_parity")
        cases = build_cases(fixture)
        self.assertEqual(len(cases), 20)
        vectors = [
            {"state": copy.deepcopy(case["before"]), "frame": case["frame"], "option": case["option"]}
            for case in cases
        ]
        base = {"gold": 100, "hp": 10, "attack": 3, "defense": 2,
                "yellow_key": 0, "blue_key": 0, "red_key": 0}
        vectors.extend([
            {"state": dict(base), "frame": 3, "option": 1},
            {"state": dict(base, gold=-1), "frame": 2, "option": 1},
            {"state": dict(base, hp=MAX_SAFE_INTEGER), "frame": 2, "option": 1},
        ])
        proc = subprocess.run(
            ["node", "--input-type=module", "-e", NODE_SCRIPT],
            input=json.dumps(vectors), text=True, capture_output=True,
            cwd=ROOT, timeout=20, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        javascript = json.loads(proc.stdout)
        self.assertEqual(len(javascript), len(vectors))
        for index, (vector, js) in enumerate(zip(vectors, javascript)):
            with self.subTest(index=index, frame=vector["frame"], option=vector["option"]):
                before = copy.deepcopy(vector["state"])
                try:
                    py = {"ok": True, "value": step_shop(vector["state"], vector["frame"], vector["option"])}
                except ValueError:
                    py = {"ok": False}
                self.assertEqual(vector["state"], before, "Python mutated the input")
                self.assertEqual(js, py)


if __name__ == "__main__":
    unittest.main()
