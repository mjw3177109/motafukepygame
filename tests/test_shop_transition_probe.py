"""Pure Python shop execution against the existing source-only vectors."""
import copy
import json
import unittest
from pathlib import Path

from core.shop_transition_probe import step_shop, MAX_SAFE_INTEGER
from tools.shop_trace_cases import build_cases

FIXTURE = Path(__file__).resolve().parents[1] / "data/original_shop_transactions_static.json"


class ShopTransitionProbeTests(unittest.TestCase):
    def test_all_twenty_static_vectors(self):
        cases = build_cases(json.loads(FIXTURE.read_text(encoding="utf-8")))
        for case in cases:
            with self.subTest(frame=case["frame"], option=case["option"], gold=case["before"]["gold"]):
                before = copy.deepcopy(case["before"])
                result = step_shop(before, case["frame"], case["option"])
                self.assertEqual(before, case["before"])
                self.assertEqual(result["state"], case["after"])
                self.assertEqual(result["success"], case["success"])
                self.assertEqual(result["provenance"], "static_actionscript_expectation_not_runtime")
                if case["option"] == 4:
                    self.assertEqual(result["exit_action"], case["exit_action"])
                    self.assertEqual(result["exit_label"], case["exit_label"])

    def test_rejects_unsupported_and_invalid_state(self):
        base = {"gold": 100, "hp": 10, "attack": 3, "defense": 2,
                "yellow_key": 0, "blue_key": 0, "red_key": 0}
        for frame, option in ((3, 1), (2, 0), (2, 5), (True, 1), (2, False)):
            with self.subTest(frame=frame, option=option), self.assertRaises(ValueError):
                step_shop(base, frame, option)
        for field, invalid in (("gold", -1), ("gold", True), ("hp", None),
                               ("attack", MAX_SAFE_INTEGER + 1)):
            state = dict(base, **{field: invalid})
            with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                step_shop(state, 2, 1)

    def test_overflow_fails_without_mutating_input(self):
        state = {"gold": 25, "hp": MAX_SAFE_INTEGER, "attack": 3, "defense": 2,
                 "yellow_key": 0, "blue_key": 0, "red_key": 0}
        before = copy.deepcopy(state)
        with self.assertRaises(ValueError):
            step_shop(state, 2, 1)
        self.assertEqual(state, before)


if __name__ == "__main__":
    unittest.main()
