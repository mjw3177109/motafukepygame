"""Regression tests for independently archived FFDec frame 34/35/54 bytes."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.audit_original_battle_transitions import (
    FRAMES, SWF_SHA256, audit_transitions, sha256,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures'


class OriginalBattleTransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scripts = {n: (FIXTURES / f'original_mt_other_04_frame{n}.as').read_bytes()
                       for n in FRAMES}

    def test_all_original_bytes_and_explicit_nonparity(self):
        for frame, anchor in FRAMES.items():
            self.assertEqual(hashlib.sha256(self.scripts[frame]).hexdigest(), anchor['sha256'])
        result = audit_transitions(self.scripts, SWF_SHA256)
        self.assertEqual([x['frame'] for x in result['sources']], [34, 35, 54])
        self.assertTrue(result['static_source_verified'])
        for gate in ('flash_playback_verified', 'death_handling_verified',
                     'full_battle_verified', 'gameplay_parity_verified',
                     'gymnasium_ready', 'kaggle_started'):
            self.assertFalse(result[gate])

    def test_rejects_swapped_swf_identity(self):
        with self.assertRaisesRegex(ValueError, 'game.swf SHA256'):
            audit_transitions(self.scripts, sha256(b'not original game.swf'))

    def test_rejects_missing_frame(self):
        with self.assertRaisesRegex(ValueError, 'exactly frame'):
            audit_transitions({34: self.scripts[34], 35: self.scripts[35]}, SWF_SHA256)

    def test_rejects_unexpected_frame(self):
        with self.assertRaisesRegex(ValueError, 'exactly frame'):
            audit_transitions({**self.scripts, 36: b'junk'}, SWF_SHA256)

    def test_rejects_changed_frame34_loop(self):
        tampered = self.scripts[34].replace(b'left_hp > 0', b'right_hp > 0')
        self.assertNotEqual(tampered, self.scripts[34])
        with self.assertRaisesRegex(ValueError, 'frame 34 ActionScript SHA256'):
            audit_transitions({**self.scripts, 34: tampered}, SWF_SHA256)

    def test_rejects_changed_frame35_sound(self):
        tampered = self.scripts[35].replace(b'music_07', b'music_08')
        self.assertNotEqual(tampered, self.scripts[35])
        with self.assertRaisesRegex(ValueError, 'frame 35 ActionScript SHA256'):
            audit_transitions({**self.scripts, 35: tampered}, SWF_SHA256)

    def test_rejects_frame54_handoff_order(self):
        tampered = self.scripts[54].replace(b'_root.Display_kill = 2;\r\n_root.Now_hp = right_hp;',
                                            b'_root.Now_hp = right_hp;\r\n_root.Display_kill = 2;')
        self.assertNotEqual(tampered, self.scripts[54])
        with self.assertRaisesRegex(ValueError, 'frame 54 ActionScript SHA256'):
            audit_transitions({**self.scripts, 54: tampered}, SWF_SHA256)

    def test_rejects_frame54_removed_stop(self):
        tampered = self.scripts[54].replace(b'stop();', b'play();')
        self.assertNotEqual(tampered, self.scripts[54])
        with self.assertRaisesRegex(ValueError, 'frame 54 ActionScript SHA256'):
            audit_transitions({**self.scripts, 54: tampered}, SWF_SHA256)

    def test_cli_fails_closed_on_nonoriginal_swf(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            scripts = base / 'export' / 'scripts' / 'DefineSprite_453_mt_other_04'
            for frame, data in self.scripts.items():
                path = scripts / f'frame_{frame}'
                path.mkdir(parents=True)
                (path / 'DoAction.as').write_bytes(data)
            (base / 'swapped.swf').write_bytes(b'not original')
            result = subprocess.run([
                sys.executable, '-m', 'tools.audit_original_battle_transitions',
                '--export-root', str(base / 'export'), '--swf', str(base / 'swapped.swf'),
                '--out', str(base / 'result.json'),
            ], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('game.swf SHA256 mismatch', result.stderr)
            self.assertFalse((base / 'result.json').exists())


if __name__ == '__main__':
    unittest.main()
