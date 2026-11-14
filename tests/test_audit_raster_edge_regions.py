"""Synthetic, dependency-free edge/interior/outside classification tests."""
import unittest
from tools.audit_raster_edge_regions import summarize_difference_regions


class RasterRegionTests(unittest.TestCase):
    def test_identical(self):
        data = bytes([20, 30, 40, 255] * 9)
        self.assertEqual(summarize_difference_regions(data, data, 3, 3)['rgba'],
                         {'edge': 0, 'interior': 0, 'outside': 0})

    def test_interior_rgb_and_alpha(self):
        left = bytearray([20, 30, 40, 255] * 9)
        right = bytearray(left)
        right[16] = 21
        right[19] = 243
        result = summarize_difference_regions(left, right, 3, 3)
        self.assertEqual(result['rgba'], {'edge': 0, 'interior': 1, 'outside': 0})
        self.assertEqual(result['alpha'], {'edge': 0, 'interior': 1, 'outside': 0})

    def test_alpha_strip_is_edge(self):
        left = bytearray([0, 0, 0, 0] * 25)
        right = bytearray(left)
        for y in range(1, 4):
            for x in range(1, 4):
                off = (y * 5 + x) * 4
                left[off:off + 4] = bytes([50, 50, 50, 255])
                right[off:off + 4] = bytes([50, 50, 50, 243 if x == 1 else 255])
        result = summarize_difference_regions(left, right, 5, 5)
        self.assertEqual(result['rgba'], {'edge': 3, 'interior': 0, 'outside': 0})
        self.assertEqual(result['alpha'], {'edge': 3, 'interior': 0, 'outside': 0})

    def test_hidden_rgb_is_outside(self):
        self.assertEqual(summarize_difference_regions(
            bytes([255, 0, 0, 0]), bytes([0, 255, 0, 0]), 1, 1)['rgba'],
            {'edge': 0, 'interior': 0, 'outside': 1})

    def test_hole_in_either_renderer_is_edge(self):
        left = bytearray([50, 50, 50, 255] * 25)
        right = bytearray(left)
        right[(1 * 5 + 2) * 4 + 3] = 0
        right[(2 * 5 + 2) * 4] = 51
        result = summarize_difference_regions(left, right, 5, 5)
        self.assertEqual(result['rgba'], {'edge': 2, 'interior': 0, 'outside': 0})
        self.assertEqual(result['alpha'], {'edge': 1, 'interior': 0, 'outside': 0})

    def test_rejects_invalid_sizes(self):
        for width, height in [(0, 1), (1, 0), (-1, 1), (1.5, 1)]:
            with self.assertRaises(ValueError):
                summarize_difference_regions(b'', b'', width, height)
        with self.assertRaises(ValueError):
            summarize_difference_regions(b'1234', b'123', 1, 1)


if __name__ == '__main__':
    unittest.main()
