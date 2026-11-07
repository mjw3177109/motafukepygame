"""Floor-00 trace adapter integration tests against committed source data."""
import json
from pathlib import Path
import unittest

from core.floor00_movement_trace import trace_committed_floor_00


SOURCE = Path(__file__).resolve().parents[1] / "data" / "original_floors.json"


class Floor00MovementTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = SOURCE.read_text(encoding="utf-8")

    def test_zero_steps_starts_at_source_pinned_hero(self):
        result = trace_committed_floor_00(
            self.original, {"yellow": 0, "blue": 0, "red": 0}, [])
        self.assertEqual(result["frames"], [])
        self.assertEqual(result["final_state"]["row"],
                         result["initial_state"]["row"])
        self.assertEqual(result["final_state"]["col"],
                         result["initial_state"]["col"])
        self.assertEqual(result["initial_state"]["grid"],
                         json.loads(self.original)["floors"]["00"])

    def test_rejects_wrong_source_pin(self):
        data = json.loads(self.original)
        data["source"]["swf_sha256"] = "invalid"
        with self.assertRaisesRegex(ValueError, "source pin mismatch"):
            trace_committed_floor_00(
                json.dumps(data), {"yellow": 0, "blue": 0, "red": 0}, [])

    def test_rejects_invalid_inventory_even_without_moves(self):
        for keys in ({"yellow": 0}, {"yellow": True, "blue": 0, "red": 0},
                     {"yellow": 2**53, "blue": 0, "red": 0}):
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                trace_committed_floor_00(self.original, keys, [])

    def test_rejects_invalid_arrow_ids(self):
        with self.assertRaises(ValueError):
            trace_committed_floor_00(
                self.original, {"yellow": 0, "blue": 0, "red": 0}, "bad")


if __name__ == "__main__":
    unittest.main()
