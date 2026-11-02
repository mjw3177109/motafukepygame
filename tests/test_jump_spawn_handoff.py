"""Cross-runtime marker-only handoff from original jump menu to hero spawn."""
import json
import unittest
from copy import deepcopy
from pathlib import Path

from core.jump_turn_replay import replay_jump_turns
from core.jump_spawn_handoff import plan_jump_spawn_handoff

BASE = Path(__file__).parent / 'fixtures'
CASES = json.loads((BASE / 'jump_turn_replay_cases.json').read_text())
MARKERS = json.loads((BASE / 'floor_spawn_markers.json').read_text())['floors']


class JumpSpawnHandoffTests(unittest.TestCase):
    def replay(self, case):
        return replay_jump_turns(case['world'], case['cursor'], case['actions'])

    def test_confirmed_and_rejected_jump_keep_redraw_blocked(self):
        for c in CASES[:2]:
            with self.subTest(c=c['name']):
                replay = self.replay(c)
                before, markers = deepcopy(replay), deepcopy(MARKERS)
                result = plan_jump_spawn_handoff(replay, MARKERS)
                self.assertEqual(result['target_floor'], c['expected_floor'])
                row, col = MARKERS[f"{c['expected_floor']:02d}"]['97'][0]
                self.assertEqual((result['spawn']['hero']['row'], result['spawn']['hero']['col']), (row, col))
                self.assertEqual(result['render_status'], 'blocked_full_map_missing')
                self.assertTrue(result['floor_refresh_pending'])
                self.assertEqual(result['key_flag'], 0)
                self.assertEqual(replay, before)
                self.assertEqual(MARKERS, markers)

    def test_cancel_and_unverified_trace_are_rejected(self):
        for c in CASES[2:]:
            with self.assertRaisesRegex(ValueError, 'pending'):
                plan_jump_spawn_handoff(self.replay(c), MARKERS)
        replay = self.replay(CASES[0])
        replay['trace'][-1]['event'] = 'jump_cancel_cleanup'
        with self.assertRaisesRegex(ValueError, 'confirmed jump'):
            plan_jump_spawn_handoff(replay, MARKERS)

    def test_missing_ambiguous_and_out_of_range_markers_fail_closed(self):
        replay = self.replay(CASES[0])
        for broken in ({}, {'20': {'97': [], '98': [], '99': []}},
                       {'20': {'97': [[0, 0], [1, 1]], '98': [], '99': []}},
                       {'20': {'97': [[11, 0]], '98': [], '99': []}},
                       {'20': {'97': [[0, 0]], '98': [[0, 0]], '99': []}}):
            with self.assertRaises(ValueError):
                plan_jump_spawn_handoff(replay, broken)
        replay['state']['now_line'] = 0
        with self.assertRaisesRegex(ValueError, '01..26'):
            plan_jump_spawn_handoff(replay, MARKERS)
