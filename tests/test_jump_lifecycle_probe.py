"""Original-script-grounded button and sprite855 state transition vectors."""
import json
import unittest
from pathlib import Path
from core.jump_lifecycle_probe import step_jump_lifecycle

CASES = json.loads((Path(__file__).parent / 'fixtures/jump_lifecycle_cases.json').read_text())


class JumpLifecycleTests(unittest.TestCase):
    def test_shared_vectors_and_input_immutability(self):
        for c in CASES:
            with self.subTest(c=c['name']):
                world = dict(display_jump=c['mode'], key_flag=c['key'], now_line=c['now'], max_line=c['max'])
                cursor = dict(now_move_id=c['selected'])
                result = step_jump_lifecycle(world, cursor, c['action'])
                self.assertEqual(result['event'], c['event'])
                self.assertEqual(result['effects'], c['effects'])
                self.assertEqual(result['state'], dict(display_jump=c['next_mode'], key_flag=c['next_key'],
                                                       now_line=c['next_now'], max_line=c['max']))
                self.assertEqual(world['display_jump'], c['mode'])
                self.assertEqual(cursor['now_move_id'], c['selected'])

    def test_confirm_then_cleanup_keeps_keyboard_locked(self):
        world = dict(display_jump=1, key_flag=0, now_line=4, max_line=10)
        confirmed = step_jump_lifecycle(world, dict(now_move_id=7), 'confirm')
        cleaned = step_jump_lifecycle(confirmed['state'], None, 'cleanup')
        self.assertEqual((cleaned['state']['now_line'], cleaned['state']['key_flag'], cleaned['state']['display_jump']), (7, 0, 0))
        self.assertIn('set_line_display:1', cleaned['effects'])

    def test_cancel_then_cleanup_restores_keyboard(self):
        world = dict(display_jump=3, key_flag=0, now_line=4, max_line=10)
        cancelled = step_jump_lifecycle(world, None, 'cancel')
        cleaned = step_jump_lifecycle(cancelled['state'], None, 'cleanup')
        self.assertEqual((cleaned['state']['now_line'], cleaned['state']['key_flag'], cleaned['state']['display_jump']), (4, 1, 0))

    def test_invalid_states_fail_closed(self):
        world = dict(display_jump=1, key_flag=0, now_line=4, max_line=10)
        for selected in (0, 21, True, None):
            with self.assertRaisesRegex(ValueError, 'selected floor'):
                step_jump_lifecycle(world, dict(now_move_id=selected), 'confirm')
        for mode, action in ((0, 'confirm'), (2, 'cancel'), (3, 'cleanup'), (1, 'cleanup')):
            with self.assertRaises(ValueError):
                step_jump_lifecycle(dict(world, display_jump=mode), None, action)
        with self.assertRaisesRegex(ValueError, 'fields required'):
            step_jump_lifecycle(dict(world, max_line=True), None, 'cancel')
