"""Cross-runtime jump-spawn contract against FFDec-derived floor data.

Floor 00 is intentionally rejected: its initial-entry arrow_id branch has not
been evidenced as equivalent to SetLineDisplay(1). Do not invent a spawn.
"""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from core.floor_spawn_probe import plan_jump_floor_spawn

ROOT = Path(__file__).resolve().parents[1]
FLOORS = json.loads((ROOT / "data/original_floors.json").read_text(encoding="utf-8"))
MARKERS = json.loads((ROOT / "tests/fixtures/floor_spawn_markers.json").read_text(encoding="utf-8"))
NODE = shutil.which("node")
JS_RUNNER = """
import {readFileSync} from 'node:fs';
import {planJumpFloorSpawn} from './web/floor_spawn_probe.mjs';
const floors = JSON.parse(readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(Object.fromEntries(
  Object.entries(floors).map(([name, matrix]) => {
    try { return [name, {ok: planJumpFloorSpawn(matrix)}]; }
    catch (error) { return [name, {error: error.message}]; }
  })
)));
"""


class OriginalFloorSpawnCrossRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(NODE, "Node.js required for cross-runtime verification")
    def test_all_27_original_floors_match_python_and_js(self):
        self.assertEqual(FLOORS["source"]["actionscript_sha256"],
                         MARKERS["map_script_sha256"])
        self.assertEqual(FLOORS["source"]["renderer_actionscript_sha256"],
                         MARKERS["source_script_sha256"])
        floors = FLOORS["floors"]
        self.assertEqual(set(floors), set(MARKERS["floors"]))
        self.assertEqual(len(floors), 27)
        expected = {}
        for name, matrix in floors.items():
            with self.subTest(floor=name):
                self.assertEqual(len(matrix), 11)
                self.assertTrue(all(len(row) == 11 for row in matrix))
                for marker in (97, 98, 99):
                    actual = [[r, c] for r, row in enumerate(matrix)
                              for c, tile in enumerate(row) if tile == marker]
                    self.assertEqual(actual, MARKERS["floors"][name][str(marker)])
                if name == "00":
                    with self.assertRaisesRegex(ValueError, "tile 97"):
                        plan_jump_floor_spawn(matrix)
                    expected[name] = {"error": "jump redraw requires exactly one original tile 97"}
                else:
                    expected[name] = {"ok": plan_jump_floor_spawn(matrix)}
        completed = subprocess.run(
            [NODE, "--input-type=module", "-e", JS_RUNNER],
            cwd=ROOT, input=json.dumps(floors), text=True,
            capture_output=True, check=True, timeout=20,
        )
        self.assertEqual(json.loads(completed.stdout), expected)


if __name__ == "__main__":
    unittest.main()
