import json
import unittest
from pathlib import Path
from core.floor_tile_plan import plan_jump_floor_tiles

ROOT = Path(__file__).resolve().parents[1]


class FloorTilePlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/original_floors.json').read_text(encoding='utf-8'))
        cls.markers = json.loads((ROOT / 'tests/fixtures/floor_spawn_markers.json').read_text(encoding='utf-8'))

    def test_all_original_maps_and_markers(self):
        self.assertEqual(set(self.data['floors']), {f'{i:02}' for i in range(27)})
        self.assertEqual(self.data['source']['swf_sha256'], '04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9')
        self.assertEqual(self.data['source']['actionscript_sha256'], self.markers['map_script_sha256'])
        for floor, matrix in self.data['floors'].items():
            self.assertEqual(len(matrix), 11)
            self.assertTrue(all(len(row) == 11 for row in matrix))
            for tile in ('97', '98', '99'):
                actual = [[r, c] for r in range(11) for c in range(11) if matrix[r][c] == int(tile)]
                self.assertEqual(actual, self.markers['floors'][floor][tile], (floor, tile))
            if floor != '00':
                plan = plan_jump_floor_tiles(matrix)
                self.assertEqual(plan['hero']['row'], self.markers['floors'][floor]['97'][0][0])
                self.assertFalse(plan['key_unlock'])
                self.assertTrue(plan['floor_refresh_pending'])

    def test_special_sprite_mappings_and_depth(self):
        matrix = [[0]*11 for _ in range(11)]
        for c, tile in enumerate((97, 98, 1, 15, 115, 120, 119, 129, 24, 179, 99)):
            matrix[0][c] = tile
        p = plan_jump_floor_tiles(matrix)
        self.assertEqual([x['source'] for x in p['placements']],
                         ['mt_99','mt_01','mt_15','mt_15','mt_20','mt_00','mt_00','mt_24','mt_00','mt_99'])
        self.assertEqual(p['placements'][0]['depth'], 1000)
        self.assertEqual(p['placements'][1]['depth'], 514)
        self.assertEqual(p['placements'][7]['instance'], 'mt_sister')
        self.assertEqual(p['placements'][2]['stop_frame'], 1)
        self.assertEqual(p['suppressed_98'], [{'row':0,'col':1}])

    def test_reject_incomplete_or_ambiguous_map(self):
        for bad in ([], [[0]*11 for _ in range(11)], [[97]*11 for _ in range(11)],
                    [[97]+[0]*10]+[[0]*11 for _ in range(9)],
                    [[97]+[0]*10]+[[0]*11 for _ in range(9)]+[[False]+[0]*10]):
            with self.assertRaises(ValueError):
                plan_jump_floor_tiles(bad)


if __name__ == '__main__':
    unittest.main()
