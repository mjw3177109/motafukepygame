"""Regression checks for source-only sprite placement timeline extraction."""
import hashlib
import unittest

from tools.audit_sprite_placements import audit, matrix, placement, snapshots, payload_bytes


def tag(offset, indent, index, label, tag_id, raw=b''):
    return (f'{offset:08x}:{" " * indent}{index}. {label:<24} '
            f'tagId= {tag_id:2} len= {len(raw):7}  ' + ' '.join(f'{b:02x}' for b in raw))


def fixture():
    rows = []
    for i, (alias, cid, shape) in enumerate([('mt_00', 223, 222), ('mt_01', 220, 219),
                                             ('mt_02', 217, 215), ('mt_03', 213, 211)]):
        base = 0x100 + i * 0x100
        rows.append(tag(base, 4, i, f'DefineSprite ({cid})', 39,
                        cid.to_bytes(2, 'little') + b'\x01\x00\x00'))
        rows.append(tag(base + 8, 6, 1, f'PlaceObject2 ({shape}) Depth: 1', 26,
                        b'\x06\x01\x00' + shape.to_bytes(2, 'little') + b'\x00'))
        rows.append(tag(base + 16, 6, 2, 'ShowFrame', 1))
    source = '\n'.join(rows)
    trace = {'schema_version': 1, 'swf_sha256': 'a'*64,
             'ffdec_tag_dump_sha256': hashlib.sha256(source.encode()).hexdigest(),
             'symbols': {alias: {'character_id': cid, 'define_offset': f'{0x100+i*0x100:08x}'}
                         for i, (alias, cid) in enumerate([('mt_00',223),('mt_01',220),('mt_02',217),('mt_03',213)])}}
    frames = {'schema_version': 1, 'swf_sha256': 'a'*64,
              'ffdec_tag_dump_sha256': trace['ffdec_tag_dump_sha256'],
              'sprites': {alias: {'character_id': v['character_id'], 'define_offset': v['define_offset'],
                                  'frame_count': 1} for alias, v in trace['symbols'].items()}}
    return source, trace, frames


class PlacementAuditTests(unittest.TestCase):
    def test_workflow_gate_is_wired(self):
        from pathlib import Path
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/swf-audit.yml').read_text()
        self.assertEqual(workflow.count("      - 'data/original_sprite_placement_anchors.json'"), 2)
        self.assertEqual(workflow.count("      - 'tests/test_audit_sprite_placements.py'"), 2)
        self.assertIn('python -m tools.audit_sprite_placements', workflow)
        self.assertIn('.swf_audit/swf_sprite_placements.json', workflow)

    def test_real_original_static_placeobject_bytes(self):
        depth, item = placement(bytes.fromhex('06 01 00 de 00 00'), None)
        self.assertEqual(depth, 1)
        self.assertEqual(item['character_id'], 222)
        self.assertEqual(item['matrix']['tx_twips'], 0)
        self.assertEqual(item['matrix']['a_fixed16'], 65536)

    def test_real_original_moving_and_clip_placements(self):
        depth, item = placement(bytes.fromhex('46 01 00 c7 00 00 04 00'), None)
        self.assertEqual(item['clip_depth'], 4)
        self.assertEqual(depth, 1)
        d2, moving = placement(bytes.fromhex('05 03 00 12 c4 01 00'),
                               {'character_id': 215, 'matrix': item['matrix'], 'clip_depth': None})
        self.assertEqual(d2, 3)
        self.assertEqual(moving['character_id'], 215)
        self.assertEqual(moving['matrix']['tx_twips'], 196)

    def test_complete_four_sprite_fixture(self):
        source, trace, frames = fixture()
        report = audit(source, trace, frames)
        self.assertEqual(report['verified_aliases'], ['mt_00', 'mt_01', 'mt_02', 'mt_03'])
        self.assertEqual(report['sprites']['mt_00']['frames'][0]['placements'][0]['character_id'], 222)
        self.assertFalse(report['visual_parity_verified'])

    def test_source_digest_mismatch_rejected(self):
        source, trace, frames = fixture()
        trace['ffdec_tag_dump_sha256'] = 'b'*64
        with self.assertRaisesRegex(ValueError, 'provenance mismatch'):
            audit(source, trace, frames)

    def test_timeline_anchor_drift_rejected(self):
        source, trace, frames = fixture()
        anchors = {'schema_version': 1, 'swf_sha256': 'a'*64,
                   'timelines': {alias: '0'*64 for alias in trace['symbols']}}
        with self.assertRaisesRegex(ValueError, 'timeline drift'):
            audit(source, trace, frames, anchors)

    def test_missing_frame_fails_closed(self):
        source, trace, frames = fixture()
        with self.assertRaisesRegex(ValueError, 'incomplete timeline'):
            snapshots('\n'.join(line for line in source.splitlines() if not line.startswith('00000110:')), 223, '00000100', 1)

    def test_duplicate_depth_without_move_rejected(self):
        with self.assertRaisesRegex(ValueError, 'lifecycle mismatch'):
            placement(bytes.fromhex('06 01 00 de 00 00'),
                      {'character_id': 222, 'matrix': matrix(b'\x00')[0], 'clip_depth': None})

    def test_truncated_tag_payload_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'truncated or nonhex'):
            payload_bytes('05 03 00 ...', 7)

    def test_unimplemented_optional_flags_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            placement(bytes.fromhex('0e 01 00 de 00 00'), None)

    def test_matrix_bitstream_truncation_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'truncated MATRIX'):
            matrix(b'\xff')


if __name__ == '__main__':
    unittest.main()
