"""Check the initial-spawn planner against committed, source-pinned floor 00.

This is static-map parity only; it does not validate the Flash runtime.
"""
from pathlib import Path
import unittest

from core.initial_spawn_probe import plan_initial_floor_spawn
from core.original_floor_json import load_original_floor_json


ROOT = Path(__file__).resolve().parents[1]


class CommittedInitialFloorTests(unittest.TestCase):
    def test_floor_00_source_pins_and_spawn(self):
        payload = load_original_floor_json((ROOT / 'data' / 'original_floors.json').read_text(encoding='utf-8'))
        source = payload['source']
        self.assertEqual(source['renderer_actionscript_sha256'],
                         '0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034')
        self.assertEqual(source['actionscript_sha256'],
                         '2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c')
        floor = payload['floors']['00']  # Do not use '0': floor IDs are zero-padded.
        self.assertEqual(plan_initial_floor_spawn(floor), {
            'hero': {'row': 9, 'col': 5, 'x': 367, 'y': 335,
                     'source': 'mt_99', 'instance': 'mt_man', 'depth': 1000},
            'suppressed_98': [{'row': 1, 'col': 5}],
        })
        self.assertNotIn(97, [tile for row in floor for tile in row])

    def test_committed_floor_00_marker_drift_fails_closed(self):
        floor = load_original_floor_json((ROOT / 'data' / 'original_floors.json').read_text(encoding='utf-8'))['floors']['00']
        for replacement in (0, 97):
            with self.subTest(replacement=replacement):
                altered = [row[:] for row in floor]
                altered[9][5] = replacement
                with self.assertRaisesRegex(ValueError, 'tile 99'):
                    plan_initial_floor_spawn(altered)


if __name__ == '__main__':
    unittest.main()
