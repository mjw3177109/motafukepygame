"""Dependency-free unit tests for controlled SVG sampling experiment helpers."""
import unittest
from tools.experiment_svg_image_rendering import make_variant, pixel_counts, registration_offsets, registration_comparison

SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,AA==" /></svg>'


class SamplingExperimentTests(unittest.TestCase):
    def test_original_bytes_untouched(self):
        self.assertIs(make_variant(SVG, 'original'), SVG)

    def test_injects_only_image_rendering_attribute(self):
        for name in ('auto', 'pixelated', 'crisp-edges'):
            modified = make_variant(SVG, name)
            self.assertEqual(modified, SVG.replace(b'<image ', f'<image image-rendering="{name}" '.encode()))
            self.assertNotEqual(modified, SVG)

    def test_rejects_unexpected_structure_or_existing_hint(self):
        with self.assertRaisesRegex(ValueError, 'structure'):
            make_variant(b'<svg/>', 'pixelated')
        with self.assertRaisesRegex(ValueError, 'structure'):
            make_variant(SVG.replace(b'</svg>', b'<image /></svg>'), 'pixelated')
        with self.assertRaisesRegex(ValueError, 'structure'):
            make_variant(SVG.replace(b'<image ', b'<image image-rendering="auto" '), 'pixelated')

    def test_rejects_unknown_variant(self):
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            make_variant(SVG, 'smooth')

    def test_pixel_differences_separate_rgb_and_alpha(self):
        a = bytearray(64 * 64 * 4)
        b = bytearray(a)
        offset = (3 * 64 + 2) * 4
        b[offset] = 12
        b[offset + 3] = 255
        result = pixel_counts(bytes(a), bytes(b))
        self.assertEqual(result['different_rgba_pixels'], 1)
        self.assertEqual(result['different_rgb_pixels'], 1)
        self.assertEqual(result['different_alpha_pixels'], 1)
        self.assertEqual(result['difference_bounds_xywh'], [2, 3, 1, 1])
        self.assertIsNone(pixel_counts(bytes(a), bytes(a))['difference_bounds_xywh'])

    def test_fractional_registration_axes_isolated(self):
        self.assertEqual(registration_offsets(15.95, 15.95), {
            'pinned': (15.95, 15.95), 'snap-x': (16.0, 15.95),
            'snap-y': (15.95, 16.0), 'snap-xy': (16.0, 16.0)})

    def test_registration_preserves_distinct_axes(self):
        offsets = registration_offsets(15.2, 16.8)
        self.assertEqual(offsets['snap-x'], (15.0, 16.8))
        self.assertEqual(offsets['snap-y'], (15.2, 17.0))
        self.assertEqual(offsets['snap-xy'], (15.0, 17.0))

    def test_integer_registration_is_noop(self):
        offsets = registration_offsets(16, 16)
        self.assertEqual(set(offsets.values()), {(16.0, 16.0)})

    def test_invalid_registration_rejected(self):
        for bad in (float('nan'), float('inf'), float('-inf'), True, '15.95', None):
            with self.subTest(bad=repr(bad)), self.assertRaisesRegex(ValueError, 'finite'):
                registration_offsets(bad, 15.95)

    def test_registration_separates_edge_alpha_from_interior_rgb(self):
        left = bytearray(64 * 64 * 4)
        right = bytearray(64 * 64 * 4)
        for y in range(16, 48):
            for x in range(16, 48):
                offset = (y * 64 + x) * 4
                left[offset:offset + 4] = bytes([80, 80, 80, 255])
                right[offset:offset + 4] = bytes([80, 80, 80, 255])
        right[(16 * 64 + 16) * 4 + 3] = 243
        right[(24 * 64 + 24) * 4] = 81
        result = registration_comparison(bytes(left), bytes(right))
        self.assertEqual(result['different_rgba_pixels'], 2)
        self.assertEqual(result['different_rgb_pixels'], 1)
        self.assertEqual(result['different_alpha_pixels'], 1)
        self.assertEqual(result['different_composited_black_pixels'], 2)
        self.assertEqual(result['different_composited_white_pixels'], 2)
        self.assertEqual(result['difference_regions']['rgba'],
                         {'edge': 1, 'interior': 1, 'outside': 0})
        self.assertEqual(result['difference_regions']['alpha'],
                         {'edge': 1, 'interior': 0, 'outside': 0})

    def test_registration_ignores_invisible_rgb_on_opaque_backdrops(self):
        left = bytearray(64 * 64 * 4)
        right = bytearray(left)
        right[0] = 255
        result = registration_comparison(bytes(left), bytes(right))
        self.assertEqual(result['different_rgba_pixels'], 1)
        self.assertEqual(result['different_invisible_rgb_pixels'], 1)
        self.assertEqual(result['different_composited_black_pixels'], 0)
        self.assertEqual(result['different_composited_white_pixels'], 0)
        self.assertEqual(result['difference_regions']['rgba']['outside'], 1)

    def test_registration_identical_rasters_have_zero_differences(self):
        pixels = bytes(64 * 64 * 4)
        result = registration_comparison(pixels, pixels)
        self.assertEqual(result['different_rgba_pixels'], 0)
        self.assertEqual(result['different_alpha_pixels'], 0)
        self.assertEqual(sum(result['difference_regions']['rgba'].values()), 0)

    def test_pixel_length_rejected(self):
        with self.assertRaisesRegex(ValueError, '64x64'):
            pixel_counts(b'abc', b'abc')


if __name__ == '__main__':
    unittest.main()
