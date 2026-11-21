"""Regression against original source-derived floor-00 marker positions."""
import unittest
from core.initial_spawn_probe import plan_initial_floor_spawn


class InitialSpawnProbeTests(unittest.TestCase):
    def setUp(self):
        # game.swf FFDec DoAction.as floor 00: tile 99 at (9,5), 98 at (1,5).
        self.floor = [[0] * 11 for _ in range(11)]
        self.floor[9][5] = 99
        self.floor[1][5] = 98

    def test_floor_00_initial_spawn(self):
        self.assertEqual(plan_initial_floor_spawn(self.floor), {
            'hero': {'row': 9, 'col': 5, 'x': 367, 'y': 335,
                     'source': 'mt_99', 'instance': 'mt_man', 'depth': 1000},
            'suppressed_98': [{'row': 1, 'col': 5}],
        })

    def test_fail_closed_on_missing_or_ambiguous_marker(self):
        self.floor[9][5] = 0
        with self.assertRaisesRegex(ValueError, 'tile 99'):
            plan_initial_floor_spawn(self.floor)
        self.floor[9][5] = 99
        self.floor[0][0] = 99
        with self.assertRaisesRegex(ValueError, 'tile 99'):
            plan_initial_floor_spawn(self.floor)

    def test_rejects_invalid_or_unsafe_matrix(self):
        for bad in (None, [], [[0] * 11] * 10, [[True] * 11 for _ in range(11)]):
            with self.subTest(bad=repr(bad)[:30]), self.assertRaises(ValueError):
                plan_initial_floor_spawn(bad)
        for bad in (2**53, -(2**53)):
            with self.subTest(bad=bad):
                matrix = [row[:] for row in self.floor]
                matrix[0][0] = bad
                with self.assertRaises(ValueError):
                    plan_initial_floor_spawn(matrix)
