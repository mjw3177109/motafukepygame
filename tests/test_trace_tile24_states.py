"""Synthetic tile-24 traces; never substitute for captured Flash execution."""
import unittest

from test_audit_tile24_branch_order import SOURCE
from tools.trace_tile24_states import trace_tile24_states


def state(**overrides):
    value = dict(tile_id=24, display_say0=0, mt_changes=0, my_love=0,
                 now_line=0, get_money=[0, 0, 0], now_key_flag=1,
                 last_game_id=0, floor20_7_5=24)
    value.update(overrides)
    return value


def branches(result):
    return [x["branch"] for x in result["trace"]]


class Tile24StateTraceTests(unittest.TestCase):
    def test_no_tile24_no_effects(self):
        original = state(tile_id=129, now_line=22, mt_changes=1)
        result = trace_tile24_states(original, SOURCE)
        self.assertEqual(result["state"], original)
        self.assertEqual(result["trace"], [])

    def test_first_and_ending_are_independent(self):
        original = state(mt_changes=1)
        result = trace_tile24_states(original, SOURCE)
        self.assertEqual(branches(result), ["initial_dialogue", "ending_state_change"])
        self.assertEqual(result["state"]["last_game_id"], 1)
        self.assertEqual(result["state"]["mt_changes"], 0)
        self.assertEqual(original["mt_changes"], 1)

    def test_love_path_with_first_item(self):
        result = trace_tile24_states(state(my_love=1, get_money=[1, 0, 0]), SOURCE)
        self.assertEqual(branches(result), ["initial_dialogue", "love_dialogue"])
        self.assertEqual(result["trace"][-1]["dialogue_command"], "say_four")
        self.assertEqual(result["state"]["floor20_7_5"], 13)

    def test_love_path_without_first_item(self):
        result = trace_tile24_states(state(display_say0=1, my_love=1), SOURCE)
        self.assertEqual(branches(result), ["love_dialogue"])
        self.assertEqual(result["trace"][0]["dialogue_command"], "say_two")

    def test_floor22_all_items(self):
        result = trace_tile24_states(state(now_line=22, get_money=[1, 1, 1]), SOURCE)
        self.assertEqual(branches(result), ["initial_dialogue", "floor22_dialogue"])
        self.assertEqual(result["trace"][-1]["dialogue_command"], "say_six")
        self.assertEqual(result["state"]["now_key_flag"], 0)

    def test_floor22_missing_item(self):
        result = trace_tile24_states(state(now_line=22, get_money=[1, 1, 0]), SOURCE)
        self.assertEqual(result["trace"][-1]["dialogue_command"], "say_five")

    def test_multiple_branches_keep_source_order(self):
        result = trace_tile24_states(state(now_line=22, my_love=1, mt_changes=1), SOURCE)
        self.assertEqual(branches(result), ["initial_dialogue", "love_dialogue", "floor22_dialogue"])
        self.assertEqual(result["state"]["mt_changes"], 0)
        self.assertEqual(result["state"]["last_game_id"], 0)
        self.assertEqual(result["trace"][-1]["dialogue_command"], "say_five")

    def test_guard_mutation_refused(self):
        changed = SOURCE.replace("_root.mt_changes == 1 &&", "_root.mt_changes == 2 &&")
        with self.assertRaises(ValueError):
            trace_tile24_states(state(), changed)

    def test_bad_input_refused_without_coercion(self):
        for changed in (state(my_love=True), state(get_money=[1, 1]),
                        state(now_line=27), state(tile_id="24")):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                trace_tile24_states(changed, SOURCE)

    def test_safe_integer_boundary_matches_javascript(self):
        maximum = (1 << 53) - 1
        for original in (state(tile_id=maximum), state(floor20_7_5=-maximum)):
            with self.subTest(original=original):
                result = trace_tile24_states(original, SOURCE)
                self.assertEqual(result["state"]["tile_id"], original["tile_id"])
                self.assertEqual(result["state"]["floor20_7_5"], original["floor20_7_5"])

    def test_unsafe_cross_language_integer_rejected_without_mutation(self):
        unsafe = 1 << 53
        for original in (state(tile_id=unsafe), state(floor20_7_5=unsafe),
                         state(floor20_7_5=-unsafe)):
            with self.subTest(original=original):
                before = {**original, "get_money": list(original["get_money"])}
                with self.assertRaises(ValueError):
                    trace_tile24_states(original, SOURCE)
                self.assertEqual(original, before)

    def test_result_cannot_claim_runtime_parity(self):
        result = trace_tile24_states(state(), SOURCE)
        self.assertTrue(result["branch_local_hypothesis_only"])
        self.assertFalse(result["flash_runtime_verified"])
        self.assertFalse(result["dual_client_parity_verified"])
        self.assertFalse(result["gymnasium_ready"])


if __name__ == "__main__":
    unittest.main()
