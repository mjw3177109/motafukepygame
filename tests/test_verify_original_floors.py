import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.verify_original_floors import verify_original_floors


def sha(data):
    return hashlib.sha256(data).hexdigest()


class VerifyOriginalFloorsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.script = 'export/scripts/frame_4346/DoAction.as'
        self.renderer = 'export/scripts/frame_4346/DoAction_2.as'
        for path, data in ((self.script, b'original map script'), (self.renderer, b'renderer script')):
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        self.floors = {f'{n:02d}': [[n] * 11 for _ in range(11)] for n in range(27)}
        self.committed = {
            'schema_version': 1, 'index_order': '[row][column] (untransposed)',
            'source': {'swf_sha256': 'a' * 64, 'actionscript_path': self.script,
                       'actionscript_sha256': sha(b'original map script'),
                       'renderer_actionscript_path': self.renderer,
                       'renderer_actionscript_sha256': sha(b'renderer script')},
            'floors': copy.deepcopy(self.floors)}
        self.extracted = {
            'schema_version': 1, 'matrix_index_order': 'outer inner (untransposed)',
            'source': {'swf_sha256': 'a' * 64, 'actionscript_path': self.script,
                       'actionscript_sha256': sha(b'original map script')},
            'floors': copy.deepcopy(self.floors)}

    def verify(self):
        return verify_original_floors(self.committed, self.extracted, self.root)

    def test_exact_static_match_does_not_claim_gameplay_parity(self):
        result = self.verify()
        self.assertEqual(result['cell_count'], 3267)
        self.assertFalse(result['visual_parity_verified'])
        self.assertFalse(result['gameplay_parity_verified'])

    def test_rejects_one_changed_cell_with_location(self):
        self.committed['floors']['12'][4][7] = 99
        with self.assertRaisesRegex(ValueError, r'12\[4\]\[7\]'):
            self.verify()

    def test_rejects_wrong_original_swf_or_script_digest(self):
        self.extracted['source']['swf_sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'swf_sha256'):
            self.verify()
        self.extracted['source']['swf_sha256'] = 'a' * 64
        (self.root / self.renderer).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.verify()

    def test_rejects_missing_script_and_traversal(self):
        (self.root / self.script).unlink()
        with self.assertRaisesRegex(ValueError, 'missing or escaped'):
            self.verify()
        self.committed['source']['actionscript_path'] = 'export/scripts/../../outside.as'
        self.extracted['source']['actionscript_path'] = self.committed['source']['actionscript_path']
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            self.verify()

    def test_rejects_incomplete_or_noninteger_matrix(self):
        del self.extracted['floors']['26']
        with self.assertRaisesRegex(ValueError, '00..26'):
            self.verify()
        self.extracted['floors'] = copy.deepcopy(self.floors)
        self.extracted['floors']['02'][1][1] = True
        with self.assertRaisesRegex(ValueError, 'integer row'):
            self.verify()


if __name__ == '__main__':
    unittest.main()
