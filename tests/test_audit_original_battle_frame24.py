"""Source-pinned tests; the fixture is FFDec export, not a Flash replay."""
import hashlib
import unittest
from pathlib import Path

from tools.audit_original_battle_frame24 import (
    SCRIPT_SHA256, SWF_SHA256, SCRIPT_PATH, audit_frame24,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/original_mt_other_04_frame24.as'


class OriginalBattleFrame24AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.swf = (ROOT / 'game.swf').read_bytes()
        cls.script = FIXTURE.read_bytes()

    def test_pinned_original_bytes(self):
        self.assertEqual(hashlib.sha256(self.swf).hexdigest(), SWF_SHA256)
        self.assertEqual(hashlib.sha256(self.script).hexdigest(), SCRIPT_SHA256)
        report = audit_frame24(self.script, self.swf)
        self.assertEqual(report['source'], SCRIPT_PATH)
        self.assertTrue(report['frame24_source_verified'])
        for gate in ('flash_replay_verified', 'full_battle_verified',
                     'gameplay_parity_verified', 'gymnasium_ready', 'kaggle_started'):
            self.assertFalse(report[gate])

    def test_rejects_swapped_inclusive_critical_boundary(self):
        altered = self.script.replace(b'kill_max <= _root.Now_life', b'kill_max < _root.Now_life')
        self.assertNotEqual(altered, self.script)
        with self.assertRaisesRegex(ValueError, 'ActionScript SHA256'):
            audit_frame24(altered, self.swf)

    def test_rejects_changed_critical_multiplier(self):
        altered = self.script.replace(b'kill_right * 2', b'kill_right * 3')
        self.assertNotEqual(altered, self.script)
        with self.assertRaisesRegex(ValueError, 'ActionScript SHA256'):
            audit_frame24(altered, self.swf)

    def test_rejects_removed_counterattack(self):
        altered = self.script.replace(b'right_hp -= kill_left;', b'right_hp -= 0;')
        self.assertNotEqual(altered, self.script)
        with self.assertRaisesRegex(ValueError, 'ActionScript SHA256'):
            audit_frame24(altered, self.swf)

    def test_rejects_changed_victory_jump(self):
        altered = self.script.replace(b'gotoAndPlay(35)', b'gotoAndPlay(34)')
        self.assertNotEqual(altered, self.script)
        with self.assertRaisesRegex(ValueError, 'ActionScript SHA256'):
            audit_frame24(altered, self.swf)

    def test_rejects_replaced_swf(self):
        with self.assertRaisesRegex(ValueError, 'game.swf SHA256'):
            audit_frame24(self.script, self.swf + b'changed')

    def test_rejects_incomplete_source(self):
        with self.assertRaisesRegex(ValueError, 'ActionScript SHA256'):
            audit_frame24(self.script[:-8], self.swf)


if __name__ == '__main__':
    unittest.main()
