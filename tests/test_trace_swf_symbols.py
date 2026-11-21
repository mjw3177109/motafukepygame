"""Fail-closed tests for FFDec symbol/shape provenance."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.trace_swf_symbols import parse_tag_dump, trace_symbols

SHA = 'a' * 64


def tag(offset, indent, index, label, tag_id, raw=b''):
    return f'{offset:08x}:{" " * indent}{index}. {label:<24} tagId= {tag_id:2} len= {len(raw):7}  ' + ' '.join(f'{b:02x}' for b in raw)


def sample():
    name = b'mt_01\x00'
    export = b'\x01\x00\x02\x00' + name
    return '\n'.join([
        tag(0x10, 4, 0, 'DefineShape (3)', 2),
        tag(0x20, 4, 1, 'DefineSprite (2)', 39),
        tag(0x21, 6, 0, 'PlaceObject2 (3) Depth: 1', 26),
        tag(0x30, 4, 2, 'ExportAssets', 56, export),
    ])


class SymbolTraceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'shapes').mkdir()
        self.shape = self.root / 'shapes/3.svg'
        self.shape.write_bytes(b'<svg/>')
        self.manifest = {'original': {'sha256': SHA}, 'files': [
            {'path': 'shapes/3.svg', 'sha256': hashlib.sha256(b'<svg/>').hexdigest()}]}
        self.coverage = {'swf_sha256': SHA, 'required_sources': ['mt_01']}
        self.anchors = {'schema_version': 1, 'swf_sha256': SHA,
                        'anchors': {'mt_01': {'character_id': 2, 'shape_ids': [3]}}}

    def trace(self, source=None, anchors=None):
        return trace_symbols(sample() if source is None else source, self.manifest,
                             self.coverage, self.root, self.anchors if anchors is None else anchors)

    def test_exact_symbol_and_hashed_shape(self):
        report = self.trace()
        self.assertEqual(report['resolved_symbol_count'], 1)
        self.assertEqual(report['unique_shape_count'], 1)
        self.assertEqual(report['symbols']['mt_01']['character_id'], 2)
        self.assertFalse(report['registration_verified'])
        self.assertFalse(report['visual_parity_verified'])

    def test_repeat_same_export_id_is_allowed(self):
        s = sample()
        s += '\n' + tag(0x40, 4, 3, 'ExportAssets', 56, b'\x01\x00\x02\x00mt_01\x00')
        self.assertEqual(len(self.trace(s)['symbols']['mt_01']['export_offsets']), 2)

    def test_conflicting_export_ids_are_rejected(self):
        s = sample() + '\n' + tag(0x40, 4, 3, 'ExportAssets', 56, b'\x01\x00\x04\x00mt_01\x00')
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            self.trace(s)

    def test_truncated_export_tag_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'payload'):
            parse_tag_dump(sample().replace('6d 74 5f 30 31 00', '6d 74 5f 30 31'))

    def test_missing_exported_shape_is_rejected(self):
        self.shape.unlink()
        with self.assertRaisesRegex(ValueError, 'shape bytes'):
            self.trace()

    def test_modified_shape_bytes_are_rejected(self):
        self.shape.write_bytes(b'<svg>changed</svg>')
        with self.assertRaisesRegex(ValueError, 'shape bytes'):
            self.trace()

    def test_anchor_drift_is_rejected(self):
        bad = json.loads(json.dumps(self.anchors))
        bad['anchors']['mt_01']['character_id'] = 999
        with self.assertRaisesRegex(ValueError, 'anchor drift'):
            self.trace(anchors=bad)

    def test_swf_source_mismatch_is_rejected(self):
        self.coverage['swf_sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'provenance mismatch'):
            self.trace()

    def test_missing_symbol_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'alias missing'):
            self.trace(sample().replace('6d 74 5f 30 31 00', '6d 74 5f 30 32 00'))


if __name__ == '__main__':
    unittest.main()
