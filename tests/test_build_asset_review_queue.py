"""Original SWF review queue must never turn source links into visual approval."""
import unittest
from tools.build_asset_review_queue import build_queue, IDENTITY

SWF = 'a' * 64
TAG = 'b' * 64
SHAPE = 'c' * 64


def fixtures():
    required = ['mt_00', 'mt_02', 'mt_99']
    coverage = {'schema_version': 1, 'swf_sha256': SWF,
                'required_sources': required, 'required_source_count': 3,
                'mapped_sources': [], 'mapped_source_count': 0,
                'missing_sources': required}
    symbols = {}
    sprites = {}
    for alias, char, count, shape in [('mt_00', 223, 1, 222),
                                      ('mt_02', 217, 10, 199), ('mt_99', 491, 74, 490)]:
        symbols[alias] = {'character_id': char, 'define_offset': '00000001',
                          'shape_exports': [{'character_id': shape,
                                             'path': f'shapes/{shape}.svg', 'sha256': SHAPE}]}
        sprites[alias] = {'character_id': char, 'define_offset': '00000001',
                          'frame_count': count, 'showframe_count': count}
    trace = {'schema_version': 1, 'swf_sha256': SWF, 'ffdec_tag_dump_sha256': TAG,
             'resolved_symbol_count': 3, 'symbols': symbols}
    frames = {'schema_version': 1, 'swf_sha256': SWF, 'ffdec_tag_dump_sha256': TAG,
              'verified_symbol_count': 3, 'frame_count_verified': True, 'sprites': sprites}
    placements = {'schema_version': 1, 'swf_sha256': SWF, 'ffdec_tag_dump_sha256': TAG,
                  'verified_aliases': ['mt_00'], 'sprites': {
                      'mt_00': {'character_id': 223, 'frame_count': 1,
                                'uninterpreted_action_count': 0,
                                'frames': [{'placements': [{'character_id': 222,
                                                            'matrix': dict(IDENTITY), 'clip_depth': None}],
                                            'uninterpreted_action_offsets': []}]}}}
    return coverage, trace, frames, placements


class ReviewQueueTests(unittest.TestCase):
    def test_static_identity_first_and_animated_unapproved(self):
        result = build_queue(*fixtures())
        self.assertEqual(result['source_alias_count'], 3)
        self.assertEqual([x['alias'] for x in result['queue']], ['mt_00', 'mt_02', 'mt_99'])
        self.assertEqual(result['review_stage_counts'], {
            'static_screenshot_review': 1, 'decode_static_placements': 0,
            'decode_animated_timeline': 2})
        self.assertFalse(result['visual_parity_verified'])
        self.assertFalse(result['gameplay_parity_verified'])
        self.assertFalse(result['gymnasium_ready'])
        self.assertFalse(result['kaggle_started'])
        self.assertTrue(all(not x['flash_visual_parity_verified'] for x in result['queue']))

    def test_unverified_static_placement_is_not_ready(self):
        coverage, trace, frames, placements = fixtures()
        placements['verified_aliases'] = []
        placements['sprites'] = {}
        result = build_queue(coverage, trace, frames, placements)
        self.assertEqual(result['queue'][0]['review_stage'], 'decode_static_placements')

    def test_subpixel_transform_needs_review_before_static_screenshot(self):
        inputs = fixtures()
        inputs[3]['sprites']['mt_00']['frames'][0]['placements'][0]['matrix']['tx_twips'] = 1
        result = build_queue(*inputs)
        self.assertEqual(result['queue'][0]['review_stage'], 'decode_static_placements')

    def test_mismatched_source_and_frame_counts_fail_closed(self):
        for index, key, value in [(1, 'swf_sha256', 'd' * 64),
                                  (2, 'ffdec_tag_dump_sha256', 'e' * 64),
                                  (2, 'verified_symbol_count', 2)]:
            with self.subTest(key=key):
                inputs = list(fixtures())
                inputs[index][key] = value
                with self.assertRaises(ValueError):
                    build_queue(*inputs)

    def test_missing_alias_or_corrupted_shape_rejected(self):
        inputs = list(fixtures())
        del inputs[1]['symbols']['mt_02']
        with self.assertRaisesRegex(ValueError, 'coverage'):
            build_queue(*inputs)
        inputs = list(fixtures())
        inputs[1]['symbols']['mt_00']['shape_exports'][0]['sha256'] = 'invalid'
        with self.assertRaisesRegex(ValueError, 'hashed shapes'):
            build_queue(*inputs)

    def test_binding_count_is_not_visual_approval(self):
        inputs = list(fixtures())
        inputs[0]['mapped_sources'] = ['mt_00']
        inputs[0]['mapped_source_count'] = 1
        inputs[0]['missing_sources'] = ['mt_02', 'mt_99']
        result = build_queue(*inputs)
        self.assertTrue(result['queue'][0]['binding_structurally_mapped'])
        self.assertFalse(result['queue'][0]['flash_visual_parity_verified'])
        self.assertFalse(result['binding_approval_inferred'])


if __name__ == '__main__':
    unittest.main()
