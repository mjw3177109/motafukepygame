"""Cross-runtime synthetic vectors grounded in FFDec arrow-button branches."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from core.jump_selection_probe import step_jump_selection

CASES = json.loads((Path(__file__).parent / "fixtures" / "jump_selection_cases.json").read_text())
WORLD = dict(key_flag=0, display_list=0, display_jump=1, display_text=0, display_buy=0, now_line=1)


class JumpSelectionTests(unittest.TestCase):
    def test_original_up_down_cursor_branches(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                world = deepcopy(WORLD)
                cursor = dict(now_move_id=case['start'], moves_x=120, moves_y=200, move_x=40)
                result = step_jump_selection(world, cursor, case['arrow_id'])
                self.assertEqual(result['cursor']['now_move_id'], case['end'])
                self.assertEqual(result['cursor']['moves_x'], 120 + case['dx'])
                self.assertEqual(result['cursor']['moves_y'], 200 + case['dy'])
                self.assertEqual(result['effects'], ['play_sound:music_11'])
                self.assertEqual(result['state'], WORLD)
                self.assertEqual(world, WORLD)
                self.assertEqual(cursor['now_move_id'], case['start'])

    def test_fail_closed_invalid_modal_or_cursor(self):
        cursor = dict(now_move_id=1, moves_x=120, moves_y=200, move_x=40)
        for world in (dict(WORLD, display_jump=0), dict(WORLD, display_buy=1)):
            with self.assertRaisesRegex(ValueError, 'inactive or shop'):
                step_jump_selection(world, cursor, 3)
        for invalid in (0, 21, True, None):
            with self.assertRaisesRegex(ValueError, 'index must'):
                step_jump_selection(WORLD, dict(cursor, now_move_id=invalid), 3)
        for invalid in (1, 2, True, '3'):
            with self.assertRaisesRegex(ValueError, 'Up'):
                step_jump_selection(WORLD, cursor, invalid)
        for invalid in (float('nan'), float('inf'), True):
            with self.assertRaisesRegex(ValueError, 'finite numeric'):
                step_jump_selection(WORLD, dict(cursor, moves_x=invalid), 3)
        with self.assertRaisesRegex(ValueError, 'gate flags'):
            step_jump_selection(dict(WORLD, display_text=None), cursor, 3)
