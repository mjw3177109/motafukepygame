"""Cross-runtime jump-menu event replay vectors, not visual or floor parity."""
import json
import unittest
from copy import deepcopy
from pathlib import Path

from core.jump_turn_replay import replay_jump_turns

CASES = json.loads((Path(__file__).parent / 'fixtures/jump_turn_replay_cases.json').read_text())


class JumpTurnReplayTests(unittest.TestCase):
    def test_shared_sequences_and_input_immutability(self):
        for c in CASES:
            with self.subTest(c=c['name']):
                world, cursor, actions = deepcopy(c['world']), deepcopy(c['cursor']), deepcopy(c['actions'])
                result = replay_jump_turns(world, cursor, actions)
                self.assertEqual([t['event'] for t in result['trace']], c['events'])
                self.assertEqual(result['state']['now_line'], c['expected_floor'])
                self.assertEqual(result['state']['display_jump'], c['expected_mode'])
                self.assertEqual(result['state']['key_flag'], c['expected_key'])
                self.assertEqual(result['cursor']['now_move_id'], c['expected_index'])
                self.assertEqual((result['cursor']['moves_x'], result['cursor']['moves_y']),
                                 (c['expected_x'], c['expected_y']))
                self.assertEqual(result['floor_refresh_pending'], c['floor_refresh_pending'])
                self.assertEqual(world, c['world'])
                self.assertEqual(cursor, c['cursor'])
                self.assertEqual(actions, c['actions'])
                self.assertEqual(result['trace'][-1]['state'], result['state'])

    def test_refuse_unimplemented_floor_redraw_and_early_cleanup(self):
        c = CASES[0]
        with self.assertRaisesRegex(ValueError, 'floor redraw not implemented'):
            replay_jump_turns(c['world'], c['cursor'], c['actions'] + [{'type': 'down'}])
        with self.assertRaisesRegex(ValueError, 'cleanup requires'):
            replay_jump_turns(c['world'], c['cursor'], [{'type': 'cleanup'}])

    def test_refuse_unsupported_actions_and_shop_priority(self):
        c = CASES[0]
        for actions in ([{'type': 'render_floor'}], [{'type': 'up', 'roll': 0}], [None]):
            with self.assertRaises(ValueError):
                replay_jump_turns(c['world'], c['cursor'], actions)
        with self.assertRaisesRegex(ValueError, 'shop modal'):
            replay_jump_turns(dict(c['world'], display_buy=1), c['cursor'], [{'type': 'up'}])

    def test_empty_actions_are_non_mutating(self):
        c = CASES[0]
        result = replay_jump_turns(c['world'], c['cursor'], [])
        self.assertEqual(result['trace'], [])
        self.assertEqual(result['state'], c['world'])
        self.assertFalse(result['floor_refresh_pending'])
