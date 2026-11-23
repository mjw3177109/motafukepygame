"""Independent expected output for the shared safe-integer map boundary."""
import unittest

from core.floor_spawn_probe import plan_jump_floor_spawn


class FloorSpawnSafeBoundaryContractTests(unittest.TestCase):
    def test_max_safe_integer_preserves_expected_spawn_and_suppression(self):
        floor = [[0 for _ in range(11)] for _ in range(11)]
        floor[0][0] = 9007199254740991
        floor[4][7] = 97
        floor[2][3] = 98
        floor[9][1] = 98
        self.assertEqual(plan_jump_floor_spawn(floor), {
            'hero': {'row': 4, 'col': 7, 'x': 431, 'y': 175,
                     'source': 'mt_99', 'instance': 'mt_man', 'depth': 1000},
            'suppressed_98': [{'row': 2, 'col': 3}, {'row': 9, 'col': 1}],
        })

    def test_negative_max_safe_integer_is_accepted_without_coercion(self):
        floor = [[0 for _ in range(11)] for _ in range(11)]
        floor[0][0] = -9007199254740991
        floor[10][10] = 97
        self.assertEqual(plan_jump_floor_spawn(floor)['hero'], {
            'row': 10, 'col': 10, 'x': 527, 'y': 367,
            'source': 'mt_99', 'instance': 'mt_man', 'depth': 1000,
        })
