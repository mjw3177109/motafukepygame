"""Regression checks for exact FFDec source sprite timeline frame counts."""
import hashlib
import unittest

from tools.audit_swf_sprite_frames import audit_sprite_frames, parse_sprite_frame_counts

SWF_SHA = 'a' * 64


def tag(offset, indent, index, label, tag_id, raw=b''):
    return (f'{offset:08x}:{" " * indent}{index}. {label:<24} '
            f'tagId= {tag_id:2} len= {len(raw):7}  ' + ' '.join(f'{b:02x}' for b in raw))


def fixture(frames=2, showframes=2, header_id=7):
    rows = [tag(0x10, 4, 1, 'DefineSprite (7)', 39,
                header_id.to_bytes(2, 'little') + frames.to_bytes(2, 'little') + b'\x00\x00')]
    rows += [tag(0x20 + i, 6, i, 'ShowFrame', 1) for i in range(showframes)]
    rows += [tag(0x40, 4, 2, 'ExportAssets', 56, b'\x00\x00')]
    return '\n'.join(rows)


def trace(source):
    return {'schema_version': 1, 'swf_sha256': SWF_SHA,
            'ffdec_tag_dump_sha256': hashlib.sha256(source.encode()).hexdigest(),
            'resolved_symbol_count': 1,
            'symbols': {'mt_01': {'character_id': 7, 'define_offset': '00000010'}}}


class SpriteFrameAuditTests(unittest.TestCase):
    def test_ci_triggers_and_report_upload_are_wired(self):
        from pathlib import Path
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/swf-audit.yml").read_text()
        self.assertEqual(workflow.count("      - 'data/original_sprite_frame_anchors.json'"), 2)
        self.assertEqual(workflow.count("      - 'tests/test_audit_swf_sprite_frames.py'"), 2)
        self.assertIn("python tools/audit_swf_sprite_frames.py --tags", workflow)
        self.assertIn(".swf_audit/swf_sprite_frames.json", workflow)

    def test_matching_source_frames_are_counted(self):
        source = fixture()
        result = audit_sprite_frames(source, trace(source), {'schema_version': 1,
            'swf_sha256': SWF_SHA, 'anchors': {'mt_01': {'character_id': 7, 'frame_count': 2}}})
        self.assertEqual(result['frame_count_histogram'], {'2': 1})
        self.assertTrue(result['frame_count_verified'])
        self.assertFalse(result['frame_content_verified'])
        self.assertFalse(result['visual_parity_verified'])

    def test_two_digit_nested_index_is_still_a_showframe(self):
        source = fixture().replace("      1. ShowFrame", "     10. ShowFrame")
        result = audit_sprite_frames(source, trace(source))
        self.assertEqual(result["sprites"]["mt_01"]["showframe_count"], 2)

    def test_missing_showframe_is_rejected(self):
        source = fixture(showframes=1)
        with self.assertRaisesRegex(ValueError, 'ShowFrame count mismatch'):
            audit_sprite_frames(source, trace(source))

    def test_extra_showframe_is_rejected(self):
        source = fixture(showframes=3)
        with self.assertRaisesRegex(ValueError, 'ShowFrame count mismatch'):
            audit_sprite_frames(source, trace(source))

    def test_truncated_define_header_is_rejected(self):
        source = fixture().replace('07 00 02 00 00 00', '07 00 02')
        with self.assertRaisesRegex(ValueError, 'truncated DefineSprite header'):
            parse_sprite_frame_counts(source)

    def test_wrong_character_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'character ID mismatch'):
            parse_sprite_frame_counts(fixture(header_id=8))

    def test_zero_frames_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'invalid or duplicate'):
            parse_sprite_frame_counts(fixture(frames=0, showframes=0))

    def test_duplicate_sprite_definition_is_rejected(self):
        source = fixture() + '\n' + tag(0x60, 4, 3, 'DefineSprite (7)', 39, b'\x07\x00\x01\x00\x00')
        with self.assertRaisesRegex(ValueError, 'invalid or duplicate'):
            parse_sprite_frame_counts(source)

    def test_source_hash_drift_is_rejected(self):
        source = fixture()
        corrupted = trace(source)
        corrupted['ffdec_tag_dump_sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
            audit_sprite_frames(source, corrupted)

    def test_anchor_drift_is_rejected(self):
        source = fixture()
        anchors = {'schema_version': 1, 'swf_sha256': SWF_SHA,
                   'anchors': {'mt_01': {'character_id': 7, 'frame_count': 10}}}
        with self.assertRaisesRegex(ValueError, 'anchor drift'):
            audit_sprite_frames(source, trace(source), anchors)

    def test_nonempty_showframe_is_rejected(self):
        source = fixture().replace('len=       0  \n', 'len=       1  ff\n', 1)
        with self.assertRaisesRegex(ValueError, 'nonempty ShowFrame'):
            parse_sprite_frame_counts(source)


if __name__ == '__main__':
    unittest.main()
