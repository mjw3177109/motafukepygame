"""Regression tests for verified screenshot byte integrity."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from tools.audit_battle_evidence import audit


class AuditBattleEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.trace = self.root / 'trace.jsonl'
        self.frame = self.root / 'flash' / 'frame.png'
        self.frame.parent.mkdir()
        Image.new('RGB', (2, 2), 'white').save(self.frame, format='PNG')
        self.row = dict(schema_version=1, source='flash', case_id='win', step=0,
                        action='initial', floor=0, x=1, y=1, hp=100, money=0,
                        exp=0, monster_id=1, monster_present=True,
                        battle_phase='idle', game_over=False,
                        evidence_frame='flash/frame.png', verified=True,
                        evidence_sha256=hashlib.sha256(self.frame.read_bytes()).hexdigest())

    def check(self):
        self.trace.write_text(json.dumps(self.row), encoding='utf-8')
        return audit(self.trace, self.root)

    def test_valid_hash(self):
        self.assertEqual(self.check(), [])

    def test_fake_png_with_matching_hash(self):
        self.frame.write_bytes(b'not a png')
        self.row['evidence_sha256'] = hashlib.sha256(self.frame.read_bytes()).hexdigest()
        self.assertIn('PNG', str(self.check()))

    def test_truncated_png_with_matching_hash(self):
        self.frame.write_bytes(self.frame.read_bytes()[:35])
        self.row['evidence_sha256'] = hashlib.sha256(self.frame.read_bytes()).hexdigest()
        self.assertIn('PNG', str(self.check()))

    def test_jpeg_renamed_png(self):
        Image.new('RGB', (2, 2), 'white').save(self.frame, format='JPEG')
        self.row['evidence_sha256'] = hashlib.sha256(self.frame.read_bytes()).hexdigest()
        self.assertIn('not PNG', str(self.check()))

    def test_missing_file(self):
        self.frame.unlink()
        self.assertIn('missing', str(self.check()))

    def test_tampered_file(self):
        self.frame.write_bytes(b'tampered')
        self.assertIn('mismatch', str(self.check()))

    def test_missing_hash(self):
        self.row.pop('evidence_sha256')
        self.assertIn('evidence_sha256', str(self.check()))

    def test_parent_traversal(self):
        self.row['evidence_frame'] = '../frame.png'
        self.assertIn('unsafe', str(self.check()))

    def test_absolute_path(self):
        self.row['evidence_frame'] = str(self.frame)
        self.assertIn('unsafe', str(self.check()))

    def test_unverified_does_not_require_hash(self):
        self.row['verified'] = False
        self.row['evidence_frame'] = None
        self.row.pop('evidence_sha256')
        self.assertEqual(self.check(), [])


if __name__ == '__main__':
    unittest.main()
