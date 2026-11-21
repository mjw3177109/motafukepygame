import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.package_swf_audit import package_exports


def digest(data):
    return hashlib.sha256(data).hexdigest()


class PackageSWFAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.exports = self.root / 'export'
        self.exports.mkdir()
        self.archive = self.root / 'audit.tar.gz'
        self.data = {
            'scripts/button/on(keyPress j).as': b'lowercase action',
            'scripts/button/on(keyPress J).as': b'UPPERCASE action',
            'images/1.png': b'png data',
        }
        for name, content in self.data.items():
            path = self.exports / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.manifest = {'original': {'sha256': 'a' * 64}, 'files': [
            {'path': name, 'size': len(content), 'sha256': digest(content)}
            for name, content in self.data.items()]}

    def test_preserves_case_colliding_scripts_and_hashes(self):
        result = package_exports(self.manifest, self.exports, self.archive)
        self.assertEqual(result['file_count'], 3)
        self.assertEqual(len(result['casefold_collision_groups']), 1)
        self.assertEqual(len(result['casefold_collision_groups'][0]), 2)
        self.assertTrue(result['archive_verified_against_manifest'])
        self.assertFalse(result['visual_parity_verified'])
        self.assertFalse(result['gameplay_parity_verified'])

    def test_rejects_changed_bytes(self):
        (self.exports / 'images/1.png').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'differs from manifest'):
            package_exports(self.manifest, self.exports, self.archive)

    def test_rejects_unlisted_or_missing_file(self):
        (self.exports / 'extra.as').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'unlisted'):
            package_exports(self.manifest, self.exports, self.archive)
        (self.exports / 'extra.as').unlink()
        (self.exports / 'images/1.png').unlink()
        with self.assertRaisesRegex(ValueError, 'missing FFDec exports'):
            package_exports(self.manifest, self.exports, self.archive)

    def test_rejects_unsafe_and_duplicate_manifest(self):
        self.manifest['files'][0]['path'] = '../outside.as'
        with self.assertRaisesRegex(ValueError, 'invalid FFDec'):
            package_exports(self.manifest, self.exports, self.archive)
        self.manifest['files'][0]['path'] = 'scripts/button/on(keyPress j).as'
        self.manifest['files'].append(dict(self.manifest['files'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate FFDec'):
            package_exports(self.manifest, self.exports, self.archive)

    def test_rejects_archive_inside_export_tree(self):
        with self.assertRaisesRegex(ValueError, 'outside export root'):
            package_exports(self.manifest, self.exports, self.exports / 'bad.tar.gz')


if __name__ == '__main__':
    unittest.main()
