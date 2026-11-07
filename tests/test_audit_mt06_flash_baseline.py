"""Synthetic-only regression tests for Flash screenshot intake."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from tools.audit_mt06_flash_baseline import audit


class FlashBaselineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.baseline = self.root / 'flash'
        self.baseline.mkdir()
        self.report, self.anchors = {}, {}
        self.pinned = {'swf_sha256': 'a' * 64, 'source_svg_sha256': 'b' * 64}
        self.mock = patch('tools.audit_mt06_flash_baseline.verify', return_value=self.pinned)
        self.mock.start()
        self.addCleanup(self.mock.stop)
        self.meta = {
            'schema_version': 1, 'alias': 'mt_06', 'swf_sha256': 'a' * 64,
            'source_svg_sha256': 'b' * 64, 'player_name': 'synthetic-test',
            'player_version': 'test', 'capture_method': 'synthetic fixture',
            'capture_utc': '2026-11-01T07:00:00Z', 'scene_id': 'synthetic-test',
            'frame_index': 12, 'crop_rect': [5, 6, 64, 64],
            'background_rgb': [255, 255, 255],
        }
        stage = Image.new('RGB', (80, 80), (255, 255, 255))
        stage.putpixel((5, 6), (100, 90, 80))
        stage.save(self.baseline / 'original_stage.png')
        stage.crop((5, 6, 69, 70)).save(self.baseline / 'reference_crop.png')
        for name, color in [('pygame', (100, 90, 80, 255)), ('chromium', (101, 90, 80, 255))]:
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            img.putpixel((0, 0), color)
            img.save(self.root / f'mt_06_{name}.png')
        self.meta['original_stage_sha256'] = self.sha('original_stage.png')
        self.meta['reference_crop_sha256'] = self.sha('reference_crop.png')
        self.write_meta()

    def sha(self, filename):
        return hashlib.sha256((self.baseline / filename).read_bytes()).hexdigest()

    def write_meta(self):
        (self.baseline / 'capture.json').write_text(json.dumps(self.meta), encoding='utf-8')

    def run_audit(self, baseline=None):
        return audit(self.report, self.anchors, self.root, self.baseline if baseline is None else baseline)

    def test_missing_baseline_is_explicit_not_success(self):
        output = self.run_audit(self.root / 'not-there')
        self.assertEqual(output['flash_capture_status'], 'missing')
        self.assertFalse(output['original_flash_reference_available'])
        self.assertFalse(output['flash_visual_parity_verified'])

    def test_exact_stage_crop_measures_both_renderers_without_approval(self):
        output = self.run_audit()
        self.assertEqual(output['pygame_vs_flash_rgb_different_pixels'], 0)
        self.assertEqual(output['chromium_vs_flash_rgb_different_pixels'], 1)
        self.assertEqual(output['flash_capture_status'], 'captured_unreviewed')
        self.assertFalse(output['runtime_binding_approved'])
        self.assertFalse(output['gymnasium_ready'])

    def test_rejects_tampered_original_stage(self):
        (self.baseline / 'original_stage.png').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self.run_audit()

    def test_rejects_edited_crop_even_with_updated_hash(self):
        Image.new('RGB', (64, 64), (1, 2, 3)).save(self.baseline / 'reference_crop.png')
        self.meta['reference_crop_sha256'] = self.sha('reference_crop.png')
        self.write_meta()
        with self.assertRaisesRegex(ValueError, 'not an exact'):
            self.run_audit()

    def test_rejects_wrong_swf_anchor(self):
        self.meta['swf_sha256'] = '0' * 64
        self.write_meta()
        with self.assertRaisesRegex(ValueError, 'provenance'):
            self.run_audit()

    def test_rejects_invalid_crop_and_frame(self):
        for field, bad in [('crop_rect', [5, 6, 63, 64]), ('crop_rect', [30, 30, 64, 64]),
                           ('frame_index', True), ('capture_utc', 'yesterday')]:
            with self.subTest(field=field, bad=bad):
                orig = copy.deepcopy(self.meta)
                self.meta[field] = bad
                self.write_meta()
                with self.assertRaises(ValueError):
                    self.run_audit()
                self.meta = orig
        self.write_meta()

    def test_rejects_capture_preapproval(self):
        self.meta['flash_visual_parity_verified'] = True
        self.write_meta()
        with self.assertRaisesRegex(ValueError, 'preapprove'):
            self.run_audit()

    def test_rejects_incomplete_existing_capture_directory(self):
        (self.baseline / 'capture.json').unlink()
        with self.assertRaisesRegex(ValueError, 'capture.json'):
            self.run_audit()

    def test_accepts_fully_opaque_rgba_stage_and_crop(self):
        with Image.open(self.baseline / 'original_stage.png') as image:
            stage = image.convert('RGBA')
        stage.save(self.baseline / 'original_stage.png')
        stage.crop((5, 6, 69, 70)).save(self.baseline / 'reference_crop.png')
        self.meta['original_stage_sha256'] = self.sha('original_stage.png')
        self.meta['reference_crop_sha256'] = self.sha('reference_crop.png')
        self.write_meta()
        output = self.run_audit()
        self.assertEqual(output['flash_capture_status'], 'captured_unreviewed')
        self.assertEqual(output['pygame_vs_flash_rgb_different_pixels'], 0)
        self.assertFalse(output['flash_visual_parity_verified'])

    def test_rejects_transparent_stage_even_when_both_hashes_match(self):
        with Image.open(self.baseline / 'original_stage.png') as image:
            stage = image.convert('RGBA')
        stage.putpixel((5, 6), (100, 90, 80, 0))
        stage.save(self.baseline / 'original_stage.png')
        stage.crop((5, 6, 69, 70)).save(self.baseline / 'reference_crop.png')
        self.meta['original_stage_sha256'] = self.sha('original_stage.png')
        self.meta['reference_crop_sha256'] = self.sha('reference_crop.png')
        self.write_meta()
        with self.assertRaisesRegex(ValueError, 'fully opaque'):
            self.run_audit()

    def test_rejects_transparent_crop_with_updated_hash(self):
        with Image.open(self.baseline / 'reference_crop.png') as image:
            crop = image.convert('RGBA')
        crop.putpixel((0, 0), (100, 90, 80, 0))
        crop.save(self.baseline / 'reference_crop.png')
        self.meta['reference_crop_sha256'] = self.sha('reference_crop.png')
        self.write_meta()
        with self.assertRaisesRegex(ValueError, 'fully opaque'):
            self.run_audit()

    def test_rejects_mode_changed_crop_even_when_rgb_pixels_match(self):
        with Image.open(self.baseline / 'original_stage.png') as image:
            stage = image.convert('RGBA')
        stage.save(self.baseline / 'original_stage.png')
        self.meta['original_stage_sha256'] = self.sha('original_stage.png')
        self.write_meta()
        with self.assertRaisesRegex(ValueError, 'not an exact raw-stage crop'):
            self.run_audit()


if __name__ == '__main__':
    unittest.main()
