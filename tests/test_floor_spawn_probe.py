"""Hero placement markers extracted from the original ActionScript tables."""
import json
import unittest
from pathlib import Path

from core.floor_spawn_probe import plan_jump_floor_spawn

DATA = json.loads((Path(__file__).parent / 'fixtures/floor_spawn_markers.json').read_text(encoding='utf-8'))


def make_floor(case):
    matrix = [[0] * 11 for _ in range(11)]
    for marker in ('97', '98', '99'):
        for row, col in case[marker]:
            matrix[row][col] = int(marker)
    return matrix


class FloorSpawnProbeTests(unittest.TestCase):
    def test_all_original_floor_markers(self):
        self.assertEqual(len(DATA['floors']), 27)
        self.assertEqual(DATA['source_script_sha256'], '0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034')
        for floor, case in DATA['floors'].items():
            with self.subTest(floor=floor):
                matrix = make_floor(case)
                if floor == '00':
                    with self.assertRaisesRegex(ValueError, 'tile 97'):
                        plan_jump_floor_spawn(matrix)
                    continue
                expected_row, expected_col = case['97'][0]
                actual = plan_jump_floor_spawn(matrix)
                self.assertEqual(actual['hero'], {
                    'row': expected_row, 'col': expected_col,
                    'x': 207 + expected_col * 32, 'y': 47 + expected_row * 32,
                    'source': 'mt_99', 'instance': 'mt_man', 'depth': 1000,
                })
                self.assertEqual(actual['suppressed_98'], [
                    {'row': row, 'col': col} for row, col in case['98']])

    def test_invalid_or_ambiguous_matrix_fails_closed(self):
        case = DATA['floors']['01']
        matrix = make_floor(case)
        for bad in (None, [], [[0] * 11] * 10, [[True] * 11 for _ in range(11)]):
            with self.assertRaises(ValueError):
                plan_jump_floor_spawn(bad)
        no_spawn = [[0] * 11 for _ in range(11)]
        with self.assertRaisesRegex(ValueError, 'tile 97'):
            plan_jump_floor_spawn(no_spawn)
        matrix[0][0] = 97
        with self.assertRaisesRegex(ValueError, 'tile 97'):
            plan_jump_floor_spawn(matrix)
