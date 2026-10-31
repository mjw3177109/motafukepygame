"""Independent synthetic fixtures: SWF RECT, SVG bounds, source and registration gates."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.audit_shape_registration import SHAPES, STATIC, IDENTITY, BitReader, audit, svg_size


def shape_tag(cid, xmin, xmax, ymin, ymax):
    values = (xmin, xmax, ymin, ymax)
    n = max(2, max((abs(x).bit_length() + 1 for x in values)))
    bits = f'{n:05b}' + ''.join(f'{x & ((1 << n) - 1):0{n}b}' for x in values)
    bits += '0' * (-len(bits) % 8)
    payload = cid.to_bytes(2, 'little') + bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
    return f'{cid:08x}:  1. DefineShape ({cid}) tagId=  2 len= {len(payload):7}  ' + ' '.join(f'{b:02x}' for b in payload)


def make_fixture(root):
    root = Path(root)
    lines, entries, shapes = [], [], {}
    for cid in SHAPES:
        lines.append(shape_tag(cid, -320, 320, -320, 320))
        rel = f'shapes/{cid}.svg'
        file = root / rel
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="32.0px" height="32.0px"/>')
        sha = hashlib.sha256(file.read_bytes()).hexdigest()
        entries.append({'path': rel, 'sha256': sha})
        shapes[cid] = sha
    tags = '\n'.join(lines)
    digest = hashlib.sha256(tags.encode()).hexdigest()
    swf = 'a' * 64
    manifest = {'original': {'sha256': swf}, 'files': entries}
    trace = {'swf_sha256': swf, 'ffdec_tag_dump_sha256': digest, 'symbols': {}}
    placements = {'swf_sha256': swf, 'ffdec_tag_dump_sha256': digest, 'sprites': {}}
    anchors = {'schema_version': 1, 'swf_sha256': swf, 'aliases': {}}
    for alias, cid in STATIC.items():
        trace['symbols'][alias] = {'shape_exports': [{'character_id': cid, 'sha256': shapes[cid]}]}
        placements['sprites'][alias] = {'frame_count': 1, 'frames': [
            {'placements': [{'depth': 1, 'character_id': cid, 'matrix': dict(IDENTITY), 'clip_depth': None}],
             'uninterpreted_action_offsets': []}]}
        anchors['aliases'][alias] = {'shape_id': cid, 'origin_x': 16, 'origin_y': 16}
    return tags, manifest, trace, placements, root, anchors


class ShapeRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.args = make_fixture(self.tmp.name)

    def test_verified_static_registration_from_rect(self):
        report = audit(*self.args)
        self.assertEqual(len(report['shapes']), 7)
        self.assertEqual(set(report['verified_static_aliases']), {'mt_00', 'mt_01'})
        self.assertEqual(report['verified_static_aliases']['mt_00']['origin_x'], 16)
        self.assertFalse(report['visual_parity_verified'])

    def test_bad_svg_hash_rejected(self):
        (Path(self.tmp.name) / 'shapes/222.svg').write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
            audit(*self.args)

    def test_svg_dimension_drift_rejected_with_valid_hash(self):
        args = copy.deepcopy(self.args)
        file = Path(self.tmp.name) / 'shapes/222.svg'
        file.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="31px" height="32px"/>')
        for entry in args[1]['files']:
            if entry['path'] == 'shapes/222.svg':
                entry['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
        args[2]['symbols']['mt_00']['shape_exports'][0]['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, 'SVG bounds differ'):
            audit(*args)

    def test_nonidentity_matrix_rejected(self):
        args = copy.deepcopy(self.args)
        args[3]['sprites']['mt_00']['frames'][0]['placements'][0]['matrix']['tx_twips'] = 1
        with self.assertRaisesRegex(ValueError, 'unverified identity'):
            audit(*args)

    def test_registration_anchor_drift_rejected(self):
        args = copy.deepcopy(self.args)
        args[5]['aliases']['mt_00']['origin_x'] = 0
        with self.assertRaisesRegex(ValueError, 'registration anchor drift'):
            audit(*args)

    def test_uninterpreted_action_rejected(self):
        args = copy.deepcopy(self.args)
        args[3]['sprites']['mt_01']['frames'][0]['uninterpreted_action_offsets'] = ['deadbeef']
        with self.assertRaisesRegex(ValueError, 'not a single-frame static'):
            audit(*args)

    def test_source_provenance_mismatch_rejected(self):
        args = copy.deepcopy(self.args)
        args[2]['ffdec_tag_dump_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'provenance mismatch'):
            audit(*args)

    def test_truncated_rect_reader_rejected(self):
        with self.assertRaisesRegex(ValueError, 'truncated'):
            BitReader(b'\x00').read(9)

    def test_svg_non_px_dimension_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsupported SVG dimension'):
            svg_size(b'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="32px"/>')

    def test_workflow_wiring(self):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/swf-audit.yml').read_text()
        self.assertIn('python -m tools.audit_shape_registration', workflow)
        self.assertIn('.swf_audit/shape_registration_report.json', workflow)
        self.assertEqual(workflow.count("      - 'data/original_shape_registration_anchors.json'"), 2)


if __name__ == '__main__':
    unittest.main()
