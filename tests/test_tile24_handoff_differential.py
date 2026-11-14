"""Differential *synthetic* tile-24 movement-to-review contract, not Flash parity.

Unlike independent language fixture assertions, these cases compare the full
Python and Node adapter outputs for identical JSON inputs. The Python-only
ActionScript source-audit flag is intentionally excluded from the comparison.
No real Flash state mapping, movie execution or ending is inferred here.
"""
import json
import subprocess
import unittest
from copy import deepcopy
from pathlib import Path

from core.tile24_handoff_preview import preview_tile24_handoff
from test_audit_tile24_branch_order import SOURCE

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests/fixtures/tile24_state_cases.json").read_text(encoding="utf-8"))
NODE_RUNNER = """
import {readFileSync} from 'node:fs';
import {previewTile24Handoff} from './web/tile24_handoff_preview.mjs';
const payload = JSON.parse(readFileSync(0, 'utf8'));
const result = previewTile24Handoff(payload.world, 2, {}, payload.review);
process.stdout.write(JSON.stringify(result));
"""


def world(tile=24, blocked=False):
    grid = [[0] * 11 for _ in range(11)]
    grid[5][6] = tile
    return {"grid": grid, "row": 5, "col": 5,
            "keys": {"yellow": 0, "blue": 0, "red": 0},
            "key_flag": 0 if blocked else 1, "display_list": 0,
            "display_jump": 0, "display_text": 0, "display_buy": 0,
            "display_kill": 0}


def run_node(w, review):
    return subprocess.run(
        ["node", "--input-type=module", "-e", NODE_RUNNER],
        input=json.dumps({"world": w, "review": review}),
        text=True, capture_output=True, cwd=ROOT, check=False,
    )


class Tile24HandoffDifferentialTests(unittest.TestCase):
    def test_shared_cases_produce_identical_non_executable_preview(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                w, review = world(), deepcopy(case["input"])
                before_world, before_review = deepcopy(w), deepcopy(review)
                node = run_node(w, review)
                if review["tile_id"] != 24:
                    with self.assertRaisesRegex(ValueError, "explicit tile-24 review state required"):
                        preview_tile24_handoff(w, 2, {}, review, SOURCE)
                    self.assertNotEqual(node.returncode, 0)
                    self.assertIn("explicit tile-24 review state required", node.stderr)
                else:
                    self.assertEqual(node.returncode, 0, node.stderr)
                    python_result = preview_tile24_handoff(w, 2, {}, review, SOURCE)
                    node_result = json.loads(node.stdout)
                    self.assertTrue(python_result["review"].pop("source_branch_order_verified"))
                    self.assertFalse(node_result["review"].pop("source_branch_order_verified"))
                    self.assertEqual(python_result, node_result)
                    self.assertFalse(python_result["executable"])
                    self.assertFalse(python_result["state_mapping_verified"])
                    self.assertFalse(python_result["flash_runtime_verified"])
                    self.assertFalse(python_result["gymnasium_ready"])
                self.assertEqual(w, before_world)
                self.assertEqual(review, before_review)

    def test_blocked_and_non_event_movement_fail_on_both_clients(self):
        review = deepcopy(next(c["input"] for c in CASES if c["name"] == "initial_only"))
        for w in (world(blocked=True), world(tile=0)):
            with self.subTest(blocked=w["key_flag"] == 0, tile=w["grid"][5][6]):
                before = deepcopy(w)
                with self.assertRaisesRegex(ValueError, "no tile-24 handoff"):
                    preview_tile24_handoff(w, 2, {}, review, SOURCE)
                node = run_node(w, review)
                self.assertNotEqual(node.returncode, 0)
                self.assertIn("no tile-24 handoff", node.stderr)
                self.assertEqual(w, before)


if __name__ == "__main__":
    unittest.main()
