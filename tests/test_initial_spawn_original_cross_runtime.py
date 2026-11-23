"""Cross-runtime floor-00 contract against the committed FFDec-derived map.

Checks static spawn planning only; Flash initialization/events remain unverified.
"""
import json
from pathlib import Path
import subprocess
import unittest

from core.initial_spawn_probe import plan_initial_floor_spawn

ROOT = Path(__file__).resolve().parents[1]
JS = """
import {planInitialFloorSpawn} from './web/initial_spawn_probe.mjs';
let raw = '';
for await (const chunk of process.stdin) raw += chunk;
const floor = JSON.parse(raw);
const before = JSON.stringify(floor);
const result = planInitialFloorSpawn(floor);
console.log(JSON.stringify({result, unchanged: JSON.stringify(floor) === before}));
"""


class OriginalFloor00CrossRuntimeTests(unittest.TestCase):
    def test_source_pinned_floor00_matches_both_planners_without_mutation(self):
        payload = json.loads((ROOT / 'data' / 'original_floors.json').read_text(encoding='utf-8'))
        self.assertEqual(
            payload['source']['renderer_actionscript_sha256'],
            '0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034',
        )
        self.assertEqual(
            payload['source']['actionscript_sha256'],
            '2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c',
        )
        floor = payload['floors']['00']
        before = json.dumps(floor)
        expected = plan_initial_floor_spawn(floor)
        self.assertEqual(json.dumps(floor), before)
        proc = subprocess.run(
            ['node', '--input-type=module', '-e', JS],
            input=json.dumps(floor), text=True, capture_output=True,
            cwd=ROOT, timeout=15, check=True,
        )
        actual = json.loads(proc.stdout)
        self.assertTrue(actual['unchanged'], 'JavaScript planner mutated original floor')
        self.assertEqual(actual['result'], expected)
        self.assertEqual(expected['hero'], {
            'row': 9, 'col': 5, 'x': 367, 'y': 335,
            'source': 'mt_99', 'instance': 'mt_man', 'depth': 1000,
        })
        self.assertEqual(expected['suppressed_98'], [{'row': 1, 'col': 5}])


if __name__ == '__main__':
    unittest.main()
