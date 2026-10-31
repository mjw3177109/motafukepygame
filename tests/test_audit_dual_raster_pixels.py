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
        self.assertIsNone(result['alpha_difference_bounds_xywh'])
        self.assertEqual(result['alpha_difference_columns'], {})
        self.assertEqual(result['alpha_value_pairs'], [])

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
        self.assertEqual(result['alpha_difference_bounds_xywh'], [0, 0, 2, 2])
        self.assertEqual(result['alpha_difference_columns'], {'0': 1, '1': 1})
        self.assertEqual(result['alpha_value_pairs'], [
            {'pygame_alpha': 255, 'chromium_alpha': 244, 'pixels': 1},
            {'pygame_alpha': 255, 'chromium_alpha': 250, 'pixels': 1}])

    def test_full_height_left_edge_alpha_strip(self):
        # Synthetic geometry regression; source PNGs are separately hash-verified in CI.
        width, height = 64, 64
        a = bytearray([0, 0, 0, 0] * (width * height))
        b = bytearray(a)
        for y in range(16, 48):
            for x in range(16, 48):
                off = (y * width + x) * 4
                a[off:off + 4] = bytes([80, 80, 80, 255])
                b[off:off + 4] = bytes([80, 80, 80, 243 if x == 16 else 255])
        result = compare_rgba(bytes(a), bytes(b), width, height)
        self.assertEqual(result['different_alpha_pixels'], 32)
        self.assertEqual(result['alpha_difference_bounds_xywh'], [16, 16, 1, 32])
        self.assertEqual(result['alpha_difference_columns'], {'16': 32})
        self.assertEqual(result['alpha_value_pairs'], [
            {'pygame_alpha': 255, 'chromium_alpha': 243, 'pixels': 32}])

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
        pins = {'mt_00': 222, 'mt_01': 219}
        entries = {name: {'source_shape_id': sid, 'source_svg_sha256': 'b' * 64,
                          'canvas_wh': [64, 64], 'png': f'{name}.png'}
                   for name, sid in pins.items()}
        pygame = {'swf_sha256': swf, 'original_svg_raster_smoke': 'passed',
                  'flash_pixel_parity_verified': False, 'sprites': entries}
        browser = {'swf_sha256': swf, 'original_html5_svg_raster_smoke': 'passed',
                   'flash_pixel_parity_verified': False,
                   'sprites': {k: dict(v) for k, v in entries.items()}}
        registration = {'schema_version': 1, 'swf_sha256': swf,
                        'registration_verified_for_static_aliases': True,
                        'visual_parity_verified': False,
                        'verified_static_aliases': {
                            alias: {'shape_id': sid, 'source': f'shapes/{sid}.svg',
                                    'sha256': 'b' * 64, 'origin_x': 15.95, 'origin_y': 15.95}
                            for alias, sid in pins.items()}}
        anchors = {'schema_version': 1, 'swf_sha256': swf,
                   'aliases': {alias: {'shape_id': sid, 'origin_x': 15.95, 'origin_y': 15.95}
                               for alias, sid in pins.items()}}
        return pygame, browser, registration, anchors

    def test_verified_provenance(self):
        p, b, registration, anchors = self.sample_reports()
        self.assertEqual(verify_reports(p, b, registration, anchors), 'a' * 64)

    def test_rejects_missing_or_drifted_source(self):
        for field, value in [('swf_sha256', 'c' * 64),
                             ('original_html5_svg_raster_smoke', 'failed'),
                             ('flash_pixel_parity_verified', True)]:
            p, b, registration, anchors = self.sample_reports()
            b[field] = value
            with self.assertRaises(ValueError):
                verify_reports(p, b, registration, anchors)
        p, b, registration, anchors = self.sample_reports()
        b['sprites']['mt_00']['source_shape_id'] = 999
        with self.assertRaises(ValueError):
            verify_reports(p, b, registration, anchors)

    def test_rejects_missing_sprite_or_png_metadata(self):
        p, b, registration, anchors = self.sample_reports()
        b['sprites'].pop('mt_01')
        with self.assertRaises(ValueError):
            verify_reports(p, b, registration, anchors)
        p, b, registration, anchors = self.sample_reports()
        b['sprites']['mt_00']['png'] = '../mt_00.png'
        with self.assertRaises(ValueError):
            verify_reports(p, b, registration, anchors)


    def test_rejects_jointly_forged_shape_id(self):
        p, b, registration, anchors = self.sample_reports()
        for report in (p, b):
            report['sprites']['mt_00']['source_shape_id'] = 999
        with self.assertRaisesRegex(ValueError, 'Shape/hash/registration mismatch'):
            verify_reports(p, b, registration, anchors)

    def test_rejects_jointly_forged_svg_hash(self):
        p, b, registration, anchors = self.sample_reports()
        for report in (p, b):
            report['sprites']['mt_01']['source_svg_sha256'] = 'c' * 64
        with self.assertRaisesRegex(ValueError, 'Shape/hash/registration mismatch'):
            verify_reports(p, b, registration, anchors)

    def test_rejects_independent_registration_or_anchor_drift(self):
        for mutation in ('source', 'origin', 'swf', 'missing'):
            p, b, registration, anchors = self.sample_reports()
            if mutation == 'source':
                registration['verified_static_aliases']['mt_00']['source'] = 'shapes/999.svg'
            elif mutation == 'origin':
                anchors['aliases']['mt_00']['origin_x'] = 0
            elif mutation == 'swf':
                anchors['swf_sha256'] = 'c' * 64
            else:
                registration.pop('registration_verified_for_static_aliases')
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                verify_reports(p, b, registration, anchors)

if __name__ == '__main__':
    unittest.main()
