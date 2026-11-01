"""Regression coverage for archived mt_06 visual-review evidence."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.audit_dual_raster_pixels import compare_rgba, inspect_rgba
from tools.build_mt06_visual_review import build


class Mt06VisualReviewTests(unittest.TestCase):
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
        for im in (self.left, self.right):
            im.putpixel((16, 16), (100, 80, 60, 255))
        self.right.putpixel((16, 16), (101, 80, 60, 255))
        self.right.putpixel((17, 16), (1, 2, 3, 200))
        for name, im in [('pygame', self.left), ('chromium', self.right)]:
            path = self.root / f'mt_06_{name}.png'
            im.save(path)
            self.report[f'{name}_png_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.report[f'{name}_alpha'] = inspect_rgba(im.tobytes())
        self.report['pygame_vs_chromium'] = compare_rgba(self.left.tobytes(), self.right.tobytes())

    def test_builds_review_with_correct_counts_and_no_flash_claim(self):
        output = build(self.report, self.anchors, self.root, self.root / 'review')
        self.assertEqual(output['different_rgba_pixels'], 2)
        self.assertEqual(output['different_alpha_pixels'], 1)
        self.assertFalse(output['original_flash_reference_available'])
        self.assertFalse(output['flash_visual_parity_verified'])
        path = self.root / 'review' / 'visual_review.png'
        with Image.open(path) as im:
            self.assertEqual(im.size, (816, 362))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), output['visual_review_png_sha256'])
        self.assertTrue((self.root / 'review' / 'visual_review.json').is_file())

    def test_rejects_tampered_png_without_writing_review(self):
        (self.root / 'mt_06_pygame.png').write_bytes(b'not a PNG')
        with self.assertRaisesRegex(ValueError, 'PNG bytes/hash'):
            build(self.report, self.anchors, self.root, self.root / 'review')
        self.assertFalse((self.root / 'review').exists())

    def test_rejects_fake_parity_gate(self):
        report = copy.deepcopy(self.report)
        report['flash_visual_parity_verified'] = True
        with self.assertRaisesRegex(ValueError, 'gate'):
            build(report, self.anchors, self.root, self.root / 'review')

    def test_rejects_false_pixel_counts(self):
        report = copy.deepcopy(self.report)
        report['pygame_vs_chromium']['different_rgba_pixels'] = 0
        with self.assertRaisesRegex(ValueError, 'comparison'):
            build(report, self.anchors, self.root, self.root / 'review')


if __name__ == '__main__':
    unittest.main()
