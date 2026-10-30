import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.audit_floor_assets import audit_floor_assets

SWF = 'a' * 64


def floor_data():
    floors = {}
    for n in range(27):
        matrix = [[0] * 11 for _ in range(11)]
        if n:
            matrix[0][0] = 97
            matrix[0][1] = 1
            matrix[0][2] = 98
        floors[f'{n:02d}'] = matrix
    return {'source': {'swf_sha256': SWF}, 'floors': floors}


def digest(data):
    return hashlib.sha256(data).hexdigest()


class FloorAssetAuditTest(unittest.TestCase):
    def test_no_mapping_is_honest_and_excludes_floor_zero(self):
        result = audit_floor_assets(floor_data())
        self.assertEqual(result['required_sources'], ['mt_01', 'mt_99'])
        self.assertEqual(result['mapped_source_count'], 0)
        self.assertEqual(result['missing_sources'], ['mt_01', 'mt_99'])
        self.assertNotIn('00', result['per_floor'])
        self.assertFalse(result['structurally_complete'])
        self.assertFalse(result['visual_parity_verified'])

    def test_hashed_mapping_is_structural_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {'images/a.png': b'PNG sample', 'scripts/evidence.as': b'Flash origin trace'}
            for path, data in files.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            manifest = {'original': {'sha256': SWF},
                        'files': [{'path': path, 'sha256': digest(data)} for path, data in files.items()]}
            binding = {'export_path': 'images/a.png', 'sha256': digest(files['images/a.png']),
                       'registration_evidence_path': 'scripts/evidence.as',
                       'registration_evidence_sha256': digest(files['scripts/evidence.as']),
                       'origin_x': 0, 'origin_y': 3.5, 'review_note': 'Manually inspected origin'}
            bindings = {'schema_version': 1, 'swf_sha256': SWF,
                        'bindings': {'mt_01': binding, 'mt_99': binding}}
            result = audit_floor_assets(floor_data(), manifest, bindings, root)
            self.assertTrue(result['structurally_complete'])
            self.assertEqual(result['mapped_source_count'], 2)
            self.assertFalse(result['visual_parity_verified'])
            (root / 'images/a.png').write_bytes(b'tampered')
            result = audit_floor_assets(floor_data(), manifest, bindings, root)
            self.assertEqual(result['mapped_source_count'], 0)
            self.assertEqual(len(result['invalid_bindings']), 2)

    def test_rejects_wrong_swf_and_unexpected_alias(self):
        manifest = {'original': {'sha256': 'b' * 64}, 'files': []}
        with self.assertRaisesRegex(ValueError, 'does not match'):
            audit_floor_assets(floor_data(), manifest)
        manifest['original']['sha256'] = SWF
        with self.assertRaisesRegex(ValueError, 'not required'):
            audit_floor_assets(floor_data(), manifest,
                               {'schema_version': 1, 'swf_sha256': SWF, 'bindings': {'mt_FAKE': {}}}, '.')

    def test_rejects_incomplete_or_corrupt_original_map(self):
        floors = floor_data()
        floors['floors']['01'][0][0] = 0
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            audit_floor_assets(floors)
        floors = floor_data()
        del floors['floors']['26']
        with self.assertRaisesRegex(ValueError, '00..26'):
            audit_floor_assets(floors)

    def test_rejects_manifest_path_traversal(self):
        manifest = {'original': {'sha256': SWF},
                    'files': [{'path': '../escape.png', 'sha256': 'a' * 64}]}
        with self.assertRaisesRegex(ValueError, 'invalid FFDec'):
            audit_floor_assets(floor_data(), manifest)


if __name__ == '__main__':
    unittest.main()
