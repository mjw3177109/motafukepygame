import unittest

from tools.verify_parity import compare
from rl.train_gate import verify


class ParityTests(unittest.TestCase):
    def test_same_trace(self):
        sample = [{"action": "up", "state": {"hp": 100}}]
        self.assertEqual(compare(sample, sample), [])

    def test_mismatch(self):
        a = [{"action": "up", "state": {"hp": 100}}]
        b = [{"action": "up", "state": {"hp": 99}}]
        self.assertEqual(compare(a, b)[0]["step"], 0)

    def test_length(self):
        self.assertEqual(compare([{"action": "a", "state": {}}], [])[0]["kind"], "length")

    def test_missing_approval_blocks_training(self):
        with self.assertRaises(ValueError):
            verify({"all_floors_verified": True})


if __name__ == "__main__":
    unittest.main()
