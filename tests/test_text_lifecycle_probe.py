"""Cross-runtime FFDec frame32/cleanup test vectors."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from core.text_lifecycle_probe import step_text_lifecycle

CASES = json.loads((Path(__file__).parent / "fixtures/text_lifecycle_cases.json").read_text(encoding="utf-8"))

class TextLifecycleTests(unittest.TestCase):
    def test_original_vectors(self):
        for case in CASES:
            with self.subTest(case=case["name"]):
                before = deepcopy(case["state"])
                if "error" in case:
                    with self.assertRaisesRegex(ValueError, case["error"]):
                        step_text_lifecycle(before, case["phase"])
                else:
                    result = step_text_lifecycle(before, case["phase"])
                    self.assertEqual(result["event"], case["event"])
                    self.assertEqual(result["effects"], case["effects"])
                    for key, value in case["expected"].items():
                        self.assertEqual(result["state"][key], value)
                self.assertEqual(before, case["state"])

    def test_two_phase_flow_keeps_boss_lock(self):
        for boss in (0, 1):
            state = {"display_text": 1, "key_flag": 0, "boss_kills": boss, "floor26_cell_3_5": 188}
            first = step_text_lifecycle(state, "frame32")
            second = step_text_lifecycle(first["state"], "cleanup")
            self.assertEqual(second["state"]["key_flag"], 0 if boss == 1 else 1)
            self.assertEqual(second["state"]["display_text"], 0)
            self.assertEqual(state["display_text"], 1)
