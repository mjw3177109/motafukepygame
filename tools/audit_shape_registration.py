"""Source-verified SWF Shape bounds, static registrations, and mt_06 candidate.

No browser/Pygame rasterization, animation or pixel parity is claimed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

TAG = re.compile(r'^([0-9a-fA-F]{8}):(\s+)\d+\.\s+(DefineShape\d*) \((\d+)\)\s+tagId=\s*(\d+)\s+len=\s*(\d+)\s*(.*)$')
HEX = re.compile(r'[0-9a-fA-F]{2}\Z')
SHAPES = (197, 199, 211, 212, 215, 216, 219, 222)
STATIC = {'mt_00': 222, 'mt_01': 219}
CANDIDATES = {'mt_06': 197}  # source registration only; not a runtime binding
IDENTITY = {'a_fixed16': 65536, 'b_fixed16': 0, 'c_fixed16': 0,
            'd_fixed16': 65536, 'tx_twips': 0, 'ty_twips': 0}


class BitReader:
    def __init__(self, data):
        self.data, self.bit = data, 0

    def read(self, width, signed=False):
        if width < 0 or self.bit + width > len(self.data) * 8:
            raise ValueError('truncated DefineShape RECT')
        value = 0
        for _ in range(width):
            value = (value << 1) | ((self.data[self.bit // 8] >> (7 - self.bit % 8)) & 1)
            self.bit += 1
        if signed and width and value & (1 << (width - 1)):
            value -= 1 << width
        return value


def parse_shape_rects(tags):
    result = {}
    for line in tags.splitlines():
        match = TAG.fullmatch(line)
        if not match:
            continue
        offset, spaces, label, cid, tag_id, length, hex_payload = match.groups()
        cid, tag_id, length = int(cid), int(tag_id), int(length)
        if cid not in SHAPES:
            continue
        if len(spaces) > 4 or tag_id not in (2, 22, 32):
            raise ValueError(f'unsupported nested or mismatched DefineShape: {cid}')
        words = hex_payload.split()
        if len(words) != length or not all(HEX.fullmatch(w) for w in words):
            raise ValueError(f'invalid original shape payload: {cid}')
        raw = bytes.fromhex(''.join(words))
        if len(raw) < 3 or int.from_bytes(raw[:2], 'little') != cid:
            raise ValueError(f'original DefineShape ID mismatch: {cid}')
        bits = BitReader(raw[2:])
        n = bits.read(5)
        if n == 0:
            raise ValueError(f'invalid RECT width: {cid}')
        xmin, xmax, ymin, ymax = (bits.read(n, True) for _ in range(4))
        if xmin >= xmax or ymin >= ymax or cid in result:
            raise ValueError(f'duplicate or invalid RECT: {cid}')
        result[cid] = {'define_offset': offset, 'rect_twips': [xmin, xmax, ymin, ymax]}
    if set(result) != set(SHAPES):
        raise ValueError(f'missing DefineShape bounds: {sorted(set(SHAPES) - set(result))}')
    return result


def svg_size(svg_bytes):
    try:
        root = ET.fromstring(svg_bytes)
    except ET.ParseError as exc:
        raise ValueError('invalid FFDec SVG') from exc
    if root.tag != '{http://www.w3.org/2000/svg}svg':
        raise ValueError('invalid SVG root')
    def dimension(name):
        raw = root.get(name, '')
        if not re.fullmatch(r'\d+(?:\.\d+)?px', raw):
            raise ValueError('unsupported SVG dimension')
        value = float(raw[:-2])
        if not math.isfinite(value) or value <= 0:
            raise ValueError('invalid SVG dimension')
        return value
    return dimension('width'), dimension('height')


def audit(tags, manifest, trace, placements, export_root, anchors):
    digest = hashlib.sha256(tags.encode('utf-8')).hexdigest()
    swf = manifest.get('original', {}).get('sha256')
    if (not isinstance(swf, str) or not re.fullmatch(r'[0-9a-f]{64}', swf) or
        trace.get('swf_sha256') != swf or placements.get('swf_sha256') != swf or
        trace.get('ffdec_tag_dump_sha256') != digest or
        placements.get('ffdec_tag_dump_sha256') != digest or
        anchors.get('schema_version') != 1 or anchors.get('swf_sha256') != swf or
        set(anchors.get('aliases', {})) != set(STATIC) or
        set(anchors.get('candidate_aliases', {})) != set(CANDIDATES)):
        raise ValueError('source or registration anchor provenance mismatch')
    inventory = {}
    for entry in manifest.get('files', []):
        if not isinstance(entry, dict) or not isinstance(entry.get('path'), str) or entry['path'] in inventory:
            raise ValueError('invalid/duplicate manifest entry')
        inventory[entry['path']] = entry.get('sha256')
    rects = parse_shape_rects(tags)
    root = Path(export_root).resolve()
    shapes = {}
    for cid, original in rects.items():
        relative = f'shapes/{cid}.svg'
        expected = inventory.get(relative)
        if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError(f'missing hashed SVG: {relative}')
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'unsafe or missing SVG: {relative}')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'SVG SHA256 mismatch: {relative}')
        width, height = svg_size(data)
        xmin, xmax, ymin, ymax = original['rect_twips']
        if abs(width - (xmax - xmin) / 20) > 1e-6 or abs(height - (ymax - ymin) / 20) > 1e-6:
            raise ValueError(f'SVG bounds differ from original RECT: {relative}')
        shapes[str(cid)] = {'path': relative, 'sha256': expected, **original,
                            'width_px': width, 'height_px': height}
    aliases, candidates = {}, {}
    for alias, cid in {**STATIC, **CANDIDATES}.items():
        sprite = placements.get('sprites', {}).get(alias, {})
        frames = sprite.get('frames', [])
        symbol = trace.get('symbols', {}).get(alias, {})
        if (len(frames) != 1 or sprite.get('frame_count') != 1 or
            len(frames[0].get('placements', [])) != 1 or
            frames[0].get('uninterpreted_action_offsets') != [] or
            len(symbol.get('shape_exports', [])) != 1):
            raise ValueError(f'not a single-frame static shape: {alias}')
        placement = frames[0]['placements'][0]
        if (placement.get('depth') != 1 or placement.get('character_id') != cid or
            placement.get('matrix') != IDENTITY or placement.get('clip_depth') is not None or
            symbol['shape_exports'][0].get('character_id') != cid or
            symbol['shape_exports'][0].get('sha256') != shapes[str(cid)]['sha256']):
            raise ValueError(f'unverified identity placement: {alias}')
        xmin, _, ymin, _ = shapes[str(cid)]['rect_twips']
        origin = {'shape_id': cid, 'origin_x': -xmin / 20, 'origin_y': -ymin / 20}
        if alias in STATIC:
            if anchors['aliases'][alias] != origin:
                raise ValueError(f'registration anchor drift: {alias}')
            aliases[alias] = {'source': shapes[str(cid)]['path'], 'sha256': shapes[str(cid)]['sha256'],
                              **origin}
        else:
            expected = {**origin, 'source_sha256': shapes[str(cid)]['sha256']}
            if anchors['candidate_aliases'][alias] != expected:
                raise ValueError(f'candidate registration anchor drift: {alias}')
            candidates[alias] = {'source': shapes[str(cid)]['path'],
                                 'sha256': shapes[str(cid)]['sha256'], **origin,
                                 'ready_for_dual_renderer_smoke': True,
                                 'flash_visual_parity_verified': False}
    return {'schema_version': 1, 'swf_sha256': swf, 'ffdec_tag_dump_sha256': digest,
            'shapes': shapes, 'verified_static_aliases': aliases,
            'static_registration_candidates': candidates,
            'registration_verified_for_static_aliases': True,
            'rasterization_verified': False, 'visual_parity_verified': False,
            'animated_registration_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('tags', 'manifest', 'trace', 'placements', 'export-root', 'anchors', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        load = lambda p: json.loads(p.read_text(encoding='utf-8'))
        result = audit(args.tags.read_text(encoding='utf-8'), load(args.manifest),
                       load(args.trace), load(args.placements), args.export_root, load(args.anchors))
    except (ValueError, KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f'Shape registration audit FAILED: {exc}\n')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('PASS: 8 source Shape RECT/SVG pairs; 2 existing static registrations; '
          '1 mt_06 source registration candidate; '
          'rasterization and pixel parity NOT VERIFIED')


if __name__ == '__main__':
    main()
