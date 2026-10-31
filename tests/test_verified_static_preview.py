"""Real loader-to-renderer integration with synthetic hashed SVG fixtures."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from core.verified_static_preview import render_verified_static_preview


class Surface:
    def __init__(self):
        self.calls = []

    def blit(self, image, xy):
        self.calls.append((image, xy))


class VerifiedStaticPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'shapes').mkdir()
        files, shapes, verified, pins = [], {}, {}, {}
        for alias, cid in [('mt_00', 222), ('mt_01', 219)]:
            path = f'shapes/{cid}.svg'
            blob = f'<svg id="{cid}"/>'.encode()
            (self.root / path).write_bytes(blob)
            digest = hashlib.sha256(blob).hexdigest()
            files.append({'path': path, 'sha256': digest})
            shapes[str(cid)] = {'path': path, 'sha256': digest}
            verified[alias] = {'shape_id': cid, 'source': path, 'sha256': digest,
                               'origin_x': 15.95, 'origin_y': 15.95}
            pins[alias] = {'shape_id': cid, 'origin_x': 15.95, 'origin_y': 15.95}
        swf = 'a' * 64
        self.report = {'schema_version': 1, 'swf_sha256': swf,
                       'registration_verified_for_static_aliases': True,
                       'verified_static_aliases': verified, 'shapes': shapes}
        self.anchors = {'schema_version': 1, 'swf_sha256': swf, 'aliases': pins}
        self.manifest = {'original': {'sha256': swf}, 'files': files}
        self.plan = {'floor_refresh_pending': True, 'key_unlock': False,
                     'placements': [
                         {'source': 'mt_00', 'instance': 'a', 'depth': 8, 'x': 48, 'y': 64},
                         {'source': 'mt_01', 'instance': 'b', 'depth': 2, 'x': 16, 'y': 32},
                     ]}
        self.surface = Surface()
        self.decoded = []

    def render(self):
        def decode(blob):
            self.decoded.append(blob)
            return blob
        return render_verified_static_preview(self.surface, self.plan,
            self.report, self.anchors, self.manifest, self.root, decoder=decode)

    def test_draws_source_order_by_depth_with_verified_registration(self):
        self.assertEqual(self.render(), 2)
        self.assertEqual([image for image, _ in self.surface.calls],
                         [b'<svg id="219"/>', b'<svg id="222"/>'])
        for actual, expected in zip([xy for _, xy in self.surface.calls],
                                    [(0.05, 16.05), (32.05, 48.05)]):
            self.assertAlmostEqual(actual[0], expected[0])
            self.assertAlmostEqual(actual[1], expected[1])
        self.assertEqual(self.plan['key_unlock'], False)
        self.assertEqual(self.plan['floor_refresh_pending'], True)

    def test_animated_alias_blocked_before_svg_read_or_draw(self):
        self.plan['placements'][1]['source'] = 'mt_02'
        with self.assertRaisesRegex(ValueError, 'unverified/animated alias'):
            self.render()
        self.assertEqual(self.decoded, [])
        self.assertEqual(self.surface.calls, [])

    def test_tampered_svg_blocks_every_draw_and_decode(self):
        (self.root / 'shapes/219.svg').write_bytes(b'altered')
        with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
            self.render()
        self.assertEqual(self.decoded, [])
        self.assertEqual(self.surface.calls, [])

    def test_invalid_placement_fails_before_first_blit(self):
        self.plan['placements'][1]['instance'] = 'a'
        with self.assertRaisesRegex(ValueError, 'duplicate sprite instance'):
            self.render()
        self.assertEqual(self.surface.calls, [])

    def test_unlocked_floor_rejected_without_decode(self):
        self.plan['key_unlock'] = True
        with self.assertRaisesRegex(ValueError, 'input-locked'):
            self.render()
        self.assertEqual(self.decoded, [])
        self.assertEqual(self.surface.calls, [])


if __name__ == '__main__':
    unittest.main()
