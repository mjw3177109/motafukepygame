"""Fail-closed mt_06 candidate provenance tests, independent of GUI dependencies."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.smoke_mt06_candidate import verify_source


class Mt06CandidateSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / 'shapes').mkdir()
        self.svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="32px" height="32px"/>'
        (root / 'shapes/197.svg').write_bytes(self.svg)
        digest = hashlib.sha256(self.svg).hexdigest()
        swf = 'a' * 64
        self.manifest = {'original': {'sha256': swf},
                         'files': [{'path': 'shapes/197.svg', 'sha256': digest}]}
        self.anchors = {'schema_version': 1, 'swf_sha256': swf,
                        'candidate_aliases': {'mt_06': {'shape_id': 197, 'origin_x': 16,
                                                       'origin_y': 16, 'source_sha256': digest}}}
        self.registration = {'schema_version': 1, 'swf_sha256': swf,
                             'registration_verified_for_static_aliases': True,
                             'visual_parity_verified': False, 'rasterization_verified': False,
                             'shapes': {'197': {'path': 'shapes/197.svg', 'sha256': digest,
                                                'rect_twips': [-320, 320, -320, 320]}},
                             'static_registration_candidates': {'mt_06': {
                                 'shape_id': 197, 'source': 'shapes/197.svg', 'sha256': digest,
                                 'origin_x': 16, 'origin_y': 16,
                                 'ready_for_dual_renderer_smoke': True,
                                 'flash_visual_parity_verified': False}}}
        self.root = root

    def verify(self, manifest=None, registration=None, anchors=None):
        return verify_source(manifest if manifest is not None else self.manifest,
                             registration if registration is not None else self.registration,
                             anchors if anchors is not None else self.anchors, self.root)

    def test_accepts_only_source_hashed_candidate(self):
        swf, digest, svg = self.verify()
        self.assertEqual(swf, 'a' * 64)
        self.assertEqual(digest, hashlib.sha256(self.svg).hexdigest())
        self.assertEqual(svg, self.svg)

    def test_refuses_changed_svg_bytes(self):
        (self.root / 'shapes/197.svg').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'SVG bytes'):
            self.verify()

    def test_refuses_wrong_shape_or_registration(self):
        for key, value in [('shape_id', 222), ('origin_x', 15.95),
                           ('ready_for_dual_renderer_smoke', False),
                           ('flash_visual_parity_verified', True)]:
            report = copy.deepcopy(self.registration)
            report['static_registration_candidates']['mt_06'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.verify(registration=report)

    def test_refuses_false_parity_claim_or_unverified_source(self):
        for key, value in [('visual_parity_verified', True),
                           ('rasterization_verified', True),
                           ('registration_verified_for_static_aliases', False)]:
            report = copy.deepcopy(self.registration)
            report[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.verify(registration=report)

    def test_refuses_manifest_hash_drift_or_duplicates(self):
        manifest = copy.deepcopy(self.manifest)
        manifest['files'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'manifest'):
            self.verify(manifest=manifest)
        manifest = copy.deepcopy(self.manifest)
        manifest['files'].append(copy.deepcopy(manifest['files'][0]))
        with self.assertRaisesRegex(ValueError, 'manifest'):
            self.verify(manifest=manifest)

    def test_refuses_anchor_or_source_dimension_drift(self):
        anchors = copy.deepcopy(self.anchors)
        anchors['candidate_aliases']['mt_06']['origin_y'] = 15.95
        with self.assertRaises(ValueError):
            self.verify(anchors=anchors)
        (self.root / 'shapes/197.svg').write_bytes(
            b'<svg xmlns="http://www.w3.org/2000/svg" width="33px" height="32px"/>')
        changed = (self.root / 'shapes/197.svg').read_bytes()
        digest = hashlib.sha256(changed).hexdigest()
        manifest = copy.deepcopy(self.manifest)
        anchors = copy.deepcopy(self.anchors)
        report = copy.deepcopy(self.registration)
        manifest['files'][0]['sha256'] = digest
        anchors['candidate_aliases']['mt_06']['source_sha256'] = digest
        report['static_registration_candidates']['mt_06']['sha256'] = digest
        report['shapes']['197']['sha256'] = digest
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            self.verify(manifest, report, anchors)


if __name__ == '__main__':
    unittest.main()
