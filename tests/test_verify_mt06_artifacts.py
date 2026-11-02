"""Independent archived mt_06 evidence verification regression tests."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.audit_dual_raster_pixels import compare_rgba, inspect_rgba
from tools.verify_mt06_artifacts import verify


class Mt06ArchivedArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        swf, svg = 'a' * 64, 'b' * 64
        self.anchors = {'schema_version': 1, 'swf_sha256': swf,
                        'candidate_aliases': {'mt_06': {'shape_id': 197,
                                                       'origin_x': 16, 'origin_y': 16,
                                                       'source_sha256': svg}}}
        self.report = {'schema_version': 1, 'alias': 'mt_06', 'shape_id': 197,
                       'swf_sha256': swf, 'source_svg_sha256': svg,
                       'chromium_version': 'test-chromium',
                       'runtime_binding_approved': False,
                       'flash_visual_parity_verified': False,
                       'gameplay_parity_verified': False,
                       'gymnasium_ready': False, 'kaggle_started': False}
        self.left = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        self.right = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        self.left.putpixel((16, 16), (100, 80, 60, 255))
        self.right.putpixel((16, 16), (101, 80, 60, 255))
        for name, img in [('pygame', self.left), ('chromium', self.right)]:
            path = self.root / f'mt_06_{name}.png'
            img.save(path)
            self.report[f'{name}_png_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.report[f'{name}_alpha'] = inspect_rgba(img.tobytes())
        self.report['pygame_vs_chromium'] = compare_rgba(self.left.tobytes(), self.right.tobytes())

    def test_accepts_exact_saved_evidence_without_parity_claim(self):
        result = verify(self.report, self.anchors, self.root)
        self.assertTrue(result['archived_png_rgba_diff_verified'])
        self.assertEqual(result['different_rgba_pixels'], 1)
        self.assertFalse(result['flash_visual_parity_verified'])

    def test_rejects_changed_png_bytes(self):
        path = self.root / 'mt_06_chromium.png'
        path.write_bytes(path.read_bytes() + b'tampered')
        with self.assertRaisesRegex(ValueError, 'PNG bytes/hash'):
            verify(self.report, self.anchors, self.root)

    def test_rejects_false_reported_diff(self):
        report = copy.deepcopy(self.report)
        report['pygame_vs_chromium']['different_rgba_pixels'] = 0
        with self.assertRaisesRegex(ValueError, 'RGBA comparison'):
            verify(report, self.anchors, self.root)

    def test_rejects_false_reported_alpha(self):
        report = copy.deepcopy(self.report)
        report['pygame_alpha']['alpha_pixels'] = 1024
        with self.assertRaisesRegex(ValueError, 'Pygame alpha'):
            verify(report, self.anchors, self.root)

    def test_rejects_wrong_png_dimensions_even_with_updated_hash(self):
        path = self.root / 'mt_06_pygame.png'
        Image.new('RGBA', (32, 32), (1, 2, 3, 255)).save(path)
        report = copy.deepcopy(self.report)
        report['pygame_png_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'canvas/mode'):
            verify(report, self.anchors, self.root)

    def test_rejects_provenance_drift_and_gate_bypass(self):
        report = copy.deepcopy(self.report)
        report['source_svg_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'provenance'):
            verify(report, self.anchors, self.root)
        for key in ('runtime_binding_approved', 'flash_visual_parity_verified',
                    'gameplay_parity_verified', 'gymnasium_ready', 'kaggle_started'):
            report = copy.deepcopy(self.report)
            report[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'gate'):
                verify(report, self.anchors, self.root)


if __name__ == '__main__':
    unittest.main()
