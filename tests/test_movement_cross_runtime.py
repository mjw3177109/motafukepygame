"""Compare complete movement outputs from Python and JavaScript on shared vectors."""
import json
import shutil
import subprocess
import unittest
from copy import deepcopy
from pathlib import Path

from core.movement_probe import DELTAS, UnsupportedTileError, step_move_arrow

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads(
    (ROOT / "tests/fixtures/movement_probe_cases.json").read_text(encoding="utf-8")
)
NODE = shutil.which("node")
NODE_RUNNER = r"""
import {readFileSync} from 'node:fs';
import {stepMoveArrow} from './web/movement_probe.mjs';

const vectors = JSON.parse(readFileSync(0, 'utf8'));
const results = vectors.map(({state, arrow}) => {
  const before = JSON.stringify(state);
  try {
    const result = stepMoveArrow(state, arrow);
    return {
      event: result.event,
      state: result.state,
      input_unchanged: JSON.stringify(state) === before,
    };
  } catch {
    return {error: true, input_unchanged: JSON.stringify(state) === before};
  }
});
process.stdout.write(JSON.stringify(results));
"""


def make_state(case):
    row, col = case.get("start", [5, 5])
    grid = [[0] * 11 for _ in range(11)]
    dr, dc = DELTAS[case["arrow"]]
    nr, nc = row + dr, col + dc
    if 0 <= nr < 11 and 0 <= nc < 11:
        grid[nr][nc] = case["tile"]
    if "origin_tile" in case:
        grid[row][col] = case["origin_tile"]
    keys = {"yellow": 0, "blue": 0, "red": 0}
    keys.update(case.get("keys", {}))
    return {
        "grid": grid,
        "row": row,
        "col": col,
        "hp": 1000,
        "attack": 10,
        "defense": 10,
        "keys": keys,
    }


class CrossRuntimeMovementParityTests(unittest.TestCase):
    @unittest.skipUnless(NODE, "Node.js is required for Python/HTML5 parity verification")
    def test_shared_vectors_match_full_state_event_and_input_immutability(self):
        vectors = []
        expected = []
        for case in CASES:
            state = make_state(case)
            before = deepcopy(state)
            vectors.append({"state": state, "arrow": case["arrow"]})
            try:
                result = step_move_arrow(state, case["arrow"])
            except UnsupportedTileError:
                expected.append({"error": True, "input_unchanged": state == before})
            else:
                expected.append({
                    "event": result["event"],
                    "state": result["state"],
                    "input_unchanged": state == before,
                })

        completed = subprocess.run(
            [NODE, "--input-type=module", "-e", NODE_RUNNER],
            cwd=ROOT,
            input=json.dumps(vectors),
            text=True,
            capture_output=True,
            check=True,
            timeout=20,
        )
        actual = json.loads(completed.stdout)
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), len(CASES))


if __name__ == "__main__":
    unittest.main()
