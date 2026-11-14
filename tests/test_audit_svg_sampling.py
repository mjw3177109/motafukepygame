"""Synthetic, dependency-free regression tests for source-bound SVG sampling inventory."""
import base64
import hashlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from tools.audit_svg_sampling import audit, inspect_svg


def png_header(width=2, height=3):
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + struct.pack('>I', len(ihdr)) +
            b'IHDR' + ihdr + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr) & 0xffffffff))


def svg(data=None):
    data = data if data is not None else png_header()
    payload = base64.b64encode(data).decode()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" width="32px" height="32px">'
            f'<defs><pattern id="p" patternUnits="userSpaceOnUse" '
            f'patternTransform="matrix(1 0 0 1 .05 .05)" width="2" height="3">'
            f'<image xlink:href="data:image/png;base64,{payload}" '
            f'width="2" height="3" style="image-rendering:pixelated"/>'
            f'</pattern></defs></svg>').encode()


class SamplingAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'shapes').mkdir()
        self.swf = 'a' * 64
        self.manifest = {'original': {'sha256': self.swf}, 'files': []}
        self.registration = {'swf_sha256': self.swf,
                             'registration_verified_for_static_aliases': True,
                             'verified_static_aliases': {}}
        for alias, cid in (('mt_00', 222), ('mt_01', 219)):
            path = f'shapes/{cid}.svg'
            content = svg()
            (self.root / path).write_bytes(content)
            sha = hashlib.sha256(content).hexdigest()
            self.manifest['files'].append({'path': path, 'sha256': sha})
            self.registration['verified_static_aliases'][alias] = {
                'shape_id': cid, 'source': path, 'sha256': sha}

    def test_source_verified_pattern_inventory(self):
        result = audit(self.manifest, self.registration, self.root)
        self.assertEqual(set(result['sprites']), {'mt_00', 'mt_01'})
        item = result['sprites']['mt_00']
        self.assertEqual(item['pattern_count'], 1)
        self.assertEqual(item['patterns'][0]['patternTransform'], 'matrix(1 0 0 1 .05 .05)')
        self.assertEqual(item['images'][0]['png_ihdr']['width'], 2)
        self.assertEqual(item['images'][0]['image_rendering'], 'pixelated')
        self.assertFalse(result['sampling_root_cause_verified'])
        self.assertFalse(result['flash_pixel_parity_verified'])

    def test_source_svg_hash_mismatch_fails(self):
        (self.root / 'shapes/222.svg').write_bytes(svg() + b' ')
        with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
            audit(self.manifest, self.registration, self.root)

    def test_independent_registration_mismatch_fails(self):
        self.registration['verified_static_aliases']['mt_00']['shape_id'] = 223
        with self.assertRaisesRegex(ValueError, 'binding mismatch'):
            audit(self.manifest, self.registration, self.root)

    def test_bad_png_ihdr_crc_fails(self):
        damaged = bytearray(png_header())
        damaged[30] ^= 1
        with self.assertRaisesRegex(ValueError, 'CRC mismatch'):
            inspect_svg(svg(bytes(damaged)))

    def test_invalid_embedded_base64_fails(self):
        with self.assertRaisesRegex(ValueError, 'base64'):
            inspect_svg(b'<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,???"/></svg>')

    def test_external_image_is_not_fetched(self):
        result = inspect_svg(b'<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.invalid/p.png"/></svg>')
        self.assertEqual(result['images'][0]['source_kind'], 'external_or_missing')
        self.assertNotIn('sha256', result['images'][0])

    def test_no_pattern_is_recorded_without_inventing_one(self):
        result = inspect_svg(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
        self.assertEqual((result['pattern_count'], result['image_count']), (0, 0))

    def test_workflow_is_wired(self):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/swf-audit.yml').read_text()
        self.assertIn('python -m tools.audit_svg_sampling', workflow)
        self.assertIn('.swf_audit/svg_sampling_report.json', workflow)


if __name__ == '__main__':
    unittest.main()
