import copy
import unittest
from core.floor_tile_plan import plan_jump_floor_tiles
from core.floor_render import blit_floor_plan, prepare_floor_draws


class FakeSurface:
    def __init__(self):
        self.calls = []

    def blit(self, image, pos):
        self.calls.append((image, pos))


class FloorRenderTest(unittest.TestCase):
    def setUp(self):
        self.matrix = [[0] * 11 for _ in range(11)]
        self.matrix[0][:4] = [97, 1, 98, 24]
        self.plan = plan_jump_floor_tiles(self.matrix)
        self.assets = {source: {'image': object(), 'origin_x': 4, 'origin_y': 7}
                       for source in {p['source'] for p in self.plan['placements']}}

    def test_draws_real_surfaces_in_depth_order_with_registration(self):
        surface = FakeSurface()
        original = copy.deepcopy(self.plan)
        count = blit_floor_plan(surface, self.plan, self.assets)
        self.assertEqual(count, 3)
        self.assertEqual([p['instance'] for p in prepare_floor_draws(self.plan, self.assets)],
                         ['mt_m_0_1', 'mt_sister', 'mt_man'])
        self.assertEqual(surface.calls[0], (self.assets['mt_01']['image'], (235, 40)))
        self.assertEqual(surface.calls[-1], (self.assets['mt_99']['image'], (203, 40)))
        self.assertEqual(self.plan, original)
        self.assertFalse(self.plan['key_unlock'])

    def test_missing_asset_rejects_without_partial_draw(self):
        surface = FakeSurface()
        del self.assets['mt_99']
        with self.assertRaisesRegex(ValueError, 'missing verified'):
            blit_floor_plan(surface, self.plan, self.assets)
        self.assertEqual(surface.calls, [])

    def test_missing_registration_rejects_without_partial_draw(self):
        surface = FakeSurface()
        del self.assets['mt_24']['origin_y']
        with self.assertRaises(ValueError):
            blit_floor_plan(surface, self.plan, self.assets)
        self.assertEqual(surface.calls, [])

    def test_rejects_unlocked_or_duplicate_instance(self):
        for bad in (dict(self.plan, key_unlock=True),
                    dict(self.plan, placements=self.plan['placements'] + [self.plan['placements'][0]])):
            with self.assertRaises(ValueError):
                prepare_floor_draws(bad, self.assets)

    def test_invalid_surface_rejected(self):
        with self.assertRaises(ValueError):
            blit_floor_plan(None, self.plan, self.assets)


if __name__ == '__main__':
    unittest.main()
