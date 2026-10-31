"""Dependency-free unit tests for controlled SVG sampling experiment helpers."""
import unittest
from tools.experiment_svg_image_rendering import make_variant, pixel_counts

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

    def test_pixel_length_rejected(self):
        with self.assertRaisesRegex(ValueError, '64x64'):
            pixel_counts(b'abc', b'abc')


if __name__ == '__main__':
    unittest.main()
