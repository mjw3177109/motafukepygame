"""Dependency-free tests for the real-SVG raster smoke gate's guardrails."""
import unittest
from tools.smoke_original_static_render import make_preview_plan, validate_visible_result


class OriginalStaticRasterSmokeTests(unittest.TestCase):
    def test_static_plan_keeps_input_locked(self):
        for alias in ('mt_00', 'mt_01'):
            plan = make_preview_plan(alias)
            self.assertTrue(plan['floor_refresh_pending'])
            self.assertFalse(plan['key_unlock'])
            self.assertEqual(plan['placements'][0]['source'], alias)
            self.assertEqual(plan['placements'][0]['depth'], 1)

    def test_rejects_animated_or_unknown_alias(self):
        for alias in ('mt_02', 'mt_03', 'mt_99', '', None):
            with self.assertRaisesRegex(ValueError, 'only two'):
                make_preview_plan(alias)

    def test_rejects_blank_or_missing_draw(self):
        for blits, pixels in ((0, 4), (1, 0), (2, 5)):
            with self.assertRaisesRegex(ValueError, 'visible pixels'):
                validate_visible_result(blits, pixels, [16, 16, 32, 32])

    def test_rejects_invalid_or_clipped_bounds(self):
        for rect in ([0, 0, 0, 2], [63, 2, 2, 2], [-1, 1, 3, 3],
                     [1, 1, 64, 2], [1, 1, 2.5, 2]):
            with self.assertRaises(ValueError):
                validate_visible_result(1, 4, rect)

    def test_accepts_visible_bounded_raster(self):
        self.assertIsNone(validate_visible_result(1, 250, [16, 16, 32, 32]))


if __name__ == '__main__':
    unittest.main()
