"""Source-scoped shop price boundaries; not Flash runtime parity."""
import copy
import unittest

from core.shop_transition_probe import step_shop


RULES = (
    (2, 1, 25, 'hp', 800),
    (2, 2, 25, 'attack', 4),
    (2, 3, 25, 'defense', 4),
    (4, 1, 10, 'yellow_key', 1),
    (4, 2, 50, 'blue_key', 1),
    (4, 3, 100, 'red_key', 1),
)
BASE = dict(gold=0, hp=10, attack=3, defense=2,
            yellow_key=0, blue_key=0, red_key=0)


class ShopPriceBoundaryTests(unittest.TestCase):
    def test_each_purchase_at_below_and_above_price(self):
        for frame, option, cost, field, delta in RULES:
            for gold in (cost - 1, cost, cost + 1):
                with self.subTest(frame=frame, option=option, gold=gold):
                    before = {**BASE, 'gold': gold}
                    snapshot = copy.deepcopy(before)
                    result = step_shop(before, frame, option)
                    expected = copy.deepcopy(snapshot)
                    success = gold >= cost
                    if success:
                        expected['gold'] -= cost
                        expected[field] += delta
                    self.assertEqual(before, snapshot, 'input must stay immutable')
                    self.assertEqual(result['state'], expected)
                    self.assertEqual(result['success'], success)
                    self.assertEqual(result['event'], 'shop_purchase' if success else 'shop_insufficient_gold')
                    self.assertEqual(result['sound'], 'music_11' if success else 'music_09')
                    self.assertEqual(result['provenance'], 'static_actionscript_expectation_not_runtime')

    def test_zero_gold_exit_has_distinct_source_actions(self):
        for frame, action in ((2, 'gotoAndPlay'), (4, 'gotoAndStop')):
            with self.subTest(frame=frame):
                before = copy.deepcopy(BASE)
                result = step_shop(before, frame, 4)
                self.assertEqual(before, BASE)
                self.assertEqual(result['state'], BASE)
                self.assertTrue(result['success'])
                self.assertEqual(result['event'], 'shop_exit')
                self.assertEqual(result['sound'], 'music_07')
                self.assertEqual(result['exit_action'], action)
                self.assertEqual(result['exit_label'], 'end')


if __name__ == '__main__':
    unittest.main()
