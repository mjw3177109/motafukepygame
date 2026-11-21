"""Initial-map event location tests; not a Flash runtime test."""
import json
import unittest
from pathlib import Path

from tools.audit_terminal_tile_locations import locate_tiles


def fixture():
    floors = {f"{i:02d}": [[0] * 11 for _ in range(11)] for i in range(27)}
    floors["19"][7][5] = 129
    floors["00"][8][5] = 24
    floors["22"][2][6] = 24
    guard = {
        "source_anchors_verified": True,
        "source_manifest_verified": True,
        "say08_start_event": {"tile_id": 129, "required_Display_say_8": 0,
                              "assigned_Display_say_8": 1, "same_guarded_block_verified": True},
        "tile_event": {"tile_id": 24, "mt_changes": 1, "my_love": 0,
                       "assigned_mt_LastGame_ID": 1, "same_guarded_block_verified": True},
    }
    return floors, guard


class TerminalTileLocationsTests(unittest.TestCase):
    def test_source_guarded_initial_positions_not_runtime_proof(self):
        floors, guard = fixture()
        result = locate_tiles(floors, guard)
        self.assertEqual(result["say08_start_tile"]["locations"],
                         [{"floor": "19", "outer_index": 7, "inner_index": 5}])
        self.assertEqual(result["ending_guard_tile"]["locations"],
                         [{"floor": "00", "outer_index": 8, "inner_index": 5},
                          {"floor": "22", "outer_index": 2, "inner_index": 6}])
        self.assertFalse(result["runtime_event_reachability_verified"])
        self.assertFalse(result["dynamic_map_mutations_verified"])
        self.assertFalse(result["gymnasium_ready"])

    def test_original_committed_initial_map_locations(self):
        path = Path(__file__).resolve().parents[1] / "data" / "original_floors.json"
        floors, guard = fixture()
        original = json.loads(path.read_text(encoding="utf-8"))["floors"]
        self.assertEqual(locate_tiles(original, guard)["say08_start_tile"]["locations"],
                         locate_tiles(floors, guard)["say08_start_tile"]["locations"])
        self.assertEqual(locate_tiles(original, guard)["ending_guard_tile"]["locations"],
                         locate_tiles(floors, guard)["ending_guard_tile"]["locations"])

    def test_moved_tile_129_fails_closed(self):
        floors, guard = fixture()
        floors["19"][7][5] = 0
        floors["18"][7][5] = 129
        with self.assertRaisesRegex(ValueError, "tile 129 locations differ"):
            locate_tiles(floors, guard)

    def test_extra_tile_24_fails_closed(self):
        floors, guard = fixture()
        floors["10"][0][0] = 24
        with self.assertRaisesRegex(ValueError, "tile 24 locations differ"):
            locate_tiles(floors, guard)

    def test_wrong_guard_fails_closed(self):
        floors, guard = fixture()
        guard["say08_start_event"]["required_Display_say_8"] = 1
        with self.assertRaisesRegex(ValueError, "guard differs"):
            locate_tiles(floors, guard)

    def test_unverified_source_fails_closed(self):
        floors, guard = fixture()
        guard["source_manifest_verified"] = False
        with self.assertRaisesRegex(ValueError, "not verified"):
            locate_tiles(floors, guard)

    def test_malformed_map_fails_closed(self):
        floors, guard = fixture()
        floors["19"][7][5] = True
        with self.assertRaisesRegex(ValueError, "invalid original floor row"):
            locate_tiles(floors, guard)


if __name__ == "__main__":
    unittest.main()
