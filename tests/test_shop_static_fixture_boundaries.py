"""Static ActionScript shop fixture regression; NOT Flash/Pygame/HTML5 parity."""
import json
import unittest
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "original_shop_transactions_static.json"
EXPECTED = {
    (2, 1): (25, "hp", 800),
    (2, 2): (25, "attack", 4),
    (2, 3): (25, "defense", 4),
    (4, 1): (10, "yellow_key", 1),
    (4, 2): (50, "blue_key", 1),
    (4, 3): (100, "red_key", 1),
}

def apply_static_reference(row, balance, stats):
    """Pure expected-state oracle from static decompilation; not game code."""
    if balance < row["cost"]:
        return balance, dict(stats)
    updated = dict(stats)
    for field, amount in row["delta"].items():
        updated[field] = updated.get(field, 0) + amount
    return balance - row["cost"], updated

class ShopStaticFixtureBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_exact_source_rules(self):
        actual = {}
        for row in self.fixture["transactions"]:
            key = (row["frame"], row["option"])
            self.assertNotIn(key, actual)
            self.assertEqual(len(row["delta"]), 1)
            field, delta = next(iter(row["delta"].items()))
            actual[key] = (row["cost"], field, delta)
        self.assertEqual(actual, EXPECTED)

    def test_balance_boundaries_without_mutation(self):
        for row in self.fixture["transactions"]:
            cost = row["cost"]
            for balance in (cost - 1, cost, cost + 1):
                with self.subTest(frame=row["frame"], option=row["option"], balance=balance):
                    stats = {"hp": 10, "attack": 3, "defense": 2,
                             "yellow_key": 0, "blue_key": 0, "red_key": 0}
                    before = dict(stats)
                    remaining, after = apply_static_reference(row, balance, stats)
                    self.assertEqual(stats, before)
                    if balance < cost:
                        self.assertEqual((remaining, after), (balance, before))
                    else:
                        self.assertEqual(remaining, balance - cost)
                        expected = dict(before)
                        for field, amount in row["delta"].items():
                            expected[field] += amount
                        self.assertEqual(after, expected)

    def test_exit_actions_and_closed_gates(self):
        exits = {(x["frame"], x["option"]): (x["condition"], x["action"], x["label"])
                 for x in self.fixture["exit"]}
        self.assertEqual(exits, {(2, 4): ("always", "gotoAndPlay", "end"),
                                 (4, 4): ("always", "gotoAndStop", "end")})
        self.assertEqual(self.fixture["verification"], "static_actionscript_only_not_runtime_parity")
        self.assertEqual(self.fixture["gates"], {
            "actionrecord_verified": False, "flash_runtime_verified": False,
            "pygame_verified": False, "html5_verified": False,
        })

if __name__ == "__main__":
    unittest.main()
