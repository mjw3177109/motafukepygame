"""Dependency-free tests for real Chromium FFDec SVG smoke gate."""
import unittest
from tools.smoke_original_browser_static import preview_plan, validate_browser_result


class BrowserStaticSmokeTests(unittest.TestCase):
    def setUp(self):
        self.result = {'draws': 1, 'canvas_wh': [64, 64], 'alpha_pixels': 1024,
                       'alpha_bounds_xywh': [16, 16, 32, 32]}
        self.reference = {'alpha_bounds_xywh': [16, 16, 32, 32]}

    def test_input_remains_locked(self):
        for alias in ('mt_00', 'mt_01'):
            p = preview_plan(alias)
            self.assertFalse(p['key_unlock'])
            self.assertTrue(p['floor_refresh_pending'])
            self.assertEqual(p['placements'][0]['source'], alias)

    def test_unverified_alias_refused(self):
        for alias in ('mt_02', 'mt_99', '', None):
            with self.assertRaises(ValueError):
                preview_plan(alias)

    def test_valid_alpha_and_small_rasterizer_difference(self):
        self.assertEqual(validate_browser_result(self.result, self.reference), [0, 0, 0, 0])
        self.result['alpha_bounds_xywh'] = [17, 15, 31, 33]
        self.assertEqual(validate_browser_result(self.result, self.reference), [1, 1, 1, 1])

    def test_blank_or_missing_draw_refused(self):
        for field, value in [('draws', 0), ('alpha_pixels', 0), ('canvas_wh', [32, 32])]:
            with self.assertRaises(ValueError):
                validate_browser_result({**self.result, field: value}, self.reference)

    def test_clipped_and_wrong_registration_refused(self):
        for box in ([63, 16, 32, 32], [0, 0, 0, 32], [5, 5, 32, 32], [16.0, 16, 32, 32]):
            with self.assertRaises(ValueError):
                validate_browser_result({**self.result, 'alpha_bounds_xywh': box}, self.reference)

    def test_missing_pygame_evidence_refused(self):
        for reference in ({}, {'alpha_bounds_xywh': [16, 16]}, None):
            with self.assertRaises(ValueError):
                validate_browser_result(self.result, reference)


if __name__ == '__main__':
    unittest.main()
