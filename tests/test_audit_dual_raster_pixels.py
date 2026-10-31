"""Dependency-free regression tests for FFDec dual-raster difference evidence."""
import unittest
from tools.audit_dual_raster_pixels import compare_rgba, inspect_rgba, verify_reports


class DualRasterAuditTests(unittest.TestCase):
    def test_identical_pixels(self):
        rgba = bytes([5, 6, 7, 255] * 4)
        result = compare_rgba(rgba, rgba, 2, 2)
        self.assertTrue(result['exact_rgba_equal'])
        self.assertEqual(result['different_rgba_pixels'], 0)
        self.assertIsNone(result['difference_bounds_xywh'])

    def test_rgb_and_alpha_separated(self):
        a = bytes([1, 2, 3, 255, 1, 2, 3, 255, 1, 2, 3, 255, 1, 2, 3, 255])
        b = bytes([2, 2, 3, 255, 1, 2, 3, 244, 1, 2, 4, 250, 1, 2, 3, 255])
        result = compare_rgba(a, b, 2, 2)
        self.assertEqual(result['different_rgba_pixels'], 3)
        self.assertEqual(result['different_rgb_pixels'], 2)
        self.assertEqual(result['different_alpha_pixels'], 2)
        self.assertEqual(result['rgb_only_different_pixels'], 1)
        self.assertEqual(result['alpha_only_different_pixels'], 1)
        self.assertEqual(result['max_abs_delta_rgba'], [1, 0, 1, 11])
        self.assertEqual(result['difference_bounds_xywh'], [0, 0, 2, 2])

    def test_rejects_different_or_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            compare_rgba(b'\x00' * 16, b'\x00' * 12, 2, 2)
        with self.assertRaises(ValueError):
            inspect_rgba(b'\x00' * 12, 2, 2)
        with self.assertRaises(ValueError):
            inspect_rgba(b'\x00' * 16, 2, 2)

    def test_alpha_bounds_and_threshold(self):
        rgba = bytes([0, 0, 0, 1, 1, 2, 3, 2, 1, 2, 3, 255, 0, 0, 0, 0])
        self.assertEqual(inspect_rgba(rgba, 2, 2),
                         {'alpha_pixels': 2, 'alpha_bounds_xywh': [0, 0, 2, 2]})

    def sample_reports(self):
        swf = 'a' * 64
        entries = {name: {'source_shape_id': sid, 'source_svg_sha256': 'b' * 64,
                          'canvas_wh': [64, 64], 'png': f'{name}.png'}
                   for name, sid in [('mt_00', 222), ('mt_01', 219)]}
        return ({'swf_sha256': swf, 'original_svg_raster_smoke': 'passed',
                 'flash_pixel_parity_verified': False, 'sprites': entries},
                {'swf_sha256': swf, 'original_html5_svg_raster_smoke': 'passed',
                 'flash_pixel_parity_verified': False,
                 'sprites': {k: dict(v) for k, v in entries.items()}})

    def test_verified_provenance(self):
        p, b = self.sample_reports()
        self.assertEqual(verify_reports(p, b), 'a' * 64)

    def test_rejects_missing_or_drifted_source(self):
        for field, value in [('swf_sha256', 'c' * 64),
                             ('original_html5_svg_raster_smoke', 'failed'),
                             ('flash_pixel_parity_verified', True)]:
            p, b = self.sample_reports()
            b[field] = value
            with self.assertRaises(ValueError):
                verify_reports(p, b)
        p, b = self.sample_reports()
        b['sprites']['mt_00']['source_shape_id'] = 999
        with self.assertRaises(ValueError):
            verify_reports(p, b)

    def test_rejects_missing_sprite_or_png_metadata(self):
        p, b = self.sample_reports()
        b['sprites'].pop('mt_01')
        with self.assertRaises(ValueError):
            verify_reports(p, b)
        p, b = self.sample_reports()
        b['sprites']['mt_00']['png'] = '../mt_00.png'
        with self.assertRaises(ValueError):
            verify_reports(p, b)


if __name__ == '__main__':
    unittest.main()
