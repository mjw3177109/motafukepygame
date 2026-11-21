"""Contract tests for the source-pinned floor-00 JSON CLI."""
import json
import subprocess
import sys
import unittest

from tools.floor00_trace_cli import run


KEYS = {"yellow": 0, "blue": 0, "red": 0}


class Floor00CliTests(unittest.TestCase):
    def test_zero_step_matches_source_pinned_spawn(self):
        result = json.loads(run({"keys": KEYS, "arrow_ids": []}))
        self.assertEqual(result["frames"], [])
        self.assertEqual(result["initial_state"], result["final_state"])
        self.assertEqual(len(result["initial_state"]["grid"]), 11)

    def test_deterministic_json_and_no_input_mutation(self):
        request = {"keys": dict(KEYS), "arrow_ids": []}
        first = run(request)
        self.assertEqual(first, run(request))
        self.assertEqual(request, {"keys": KEYS, "arrow_ids": []})

    def test_rejects_bad_contract(self):
        for request in ({"keys": KEYS}, {"keys": KEYS, "arrow_ids": [], "grid": []},
                        {"keys": KEYS, "arrow_ids": "bad"},
                        {"keys": {"yellow": True, "blue": 0, "red": 0}, "arrow_ids": []}):
            with self.subTest(request=request), self.assertRaises(ValueError):
                run(request)

    def test_module_cli_round_trip(self):
        request = {"keys": KEYS, "arrow_ids": []}
        proc = subprocess.run([sys.executable, "-m", "tools.floor00_trace_cli"],
                              input=json.dumps(request), text=True,
                              capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), run(request))

    def test_duplicate_keys_rejected_by_cli(self):
        proc = subprocess.run([sys.executable, "-m", "tools.floor00_trace_cli"],
                              input='{"keys":{"yellow":0,"yellow":1,"blue":0,"red":0},"arrow_ids":[]}',
                              text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("duplicate JSON key", proc.stderr)
        self.assertFalse(proc.stdout)


if __name__ == "__main__":
    unittest.main()
