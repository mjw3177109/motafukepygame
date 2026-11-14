"""Cross-runtime contract for FFDec-derived floor-00 static spawn planning.

Synthetic boundary fixtures only; not proof of Flash runtime parity.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.initial_spawn_probe import plan_initial_floor_spawn

JS_RUNNER = """import {planInitialFloorSpawn} from './web/initial_spawn_probe.mjs';
let raw = '';
for await (const chunk of process.stdin) raw += chunk;
const matrices = JSON.parse(raw);
console.log(JSON.stringify(matrices.map(matrix => {
  try { return {ok: true, value: planInitialFloorSpawn(matrix)}; }
  catch (error) { return {ok: false}; }
})));
"""


class InitialSpawnCrossRuntimeTests(unittest.TestCase):
    def test_python_and_html5_planners_agree_on_boundaries(self):
        base = [[0] * 11 for _ in range(11)]
        base[9][5] = 99
        base[1][5] = 98
        cases = [base]
        corners = copy.deepcopy(base)
        corners[9][5] = 0
        corners[0][0] = 99
        corners[10][10] = 98
        cases.append(corners)
        missing = copy.deepcopy(base)
        missing[9][5] = 0
        cases.append(missing)
        duplicate = copy.deepcopy(base)
        duplicate[0][0] = 99
        cases.append(duplicate)
        invalid_bool = copy.deepcopy(base)
        invalid_bool[0][0] = True
        cases.append(invalid_bool)
        invalid_large = copy.deepcopy(base)
        invalid_large[0][0] = 2**53
        cases.append(invalid_large)
        cases.append([[0] * 11 for _ in range(10)])
        expected = []
        for matrix in cases:
            before = copy.deepcopy(matrix)
            try:
                expected.append({'ok': True, 'value': plan_initial_floor_spawn(matrix)})
            except ValueError:
                expected.append({'ok': False})
            self.assertEqual(matrix, before, 'Python planner must not mutate source map')
        process = subprocess.run(
            ['node', '--input-type=module', '-e', JS_RUNNER],
            input=json.dumps(cases), text=True, capture_output=True,
            cwd=ROOT, timeout=15, check=True,
        )
        self.assertEqual(json.loads(process.stdout), expected)
        self.assertEqual(expected[0]['value']['suppressed_98'], [{'row': 1, 'col': 5}])
        self.assertEqual(expected[1]['value']['suppressed_98'],
                         [{'row': 1, 'col': 5}, {'row': 10, 'col': 10}])


if __name__ == '__main__':
    unittest.main()
