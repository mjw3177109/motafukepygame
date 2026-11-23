"""Inventory source-verified FFDec SVG bitmap/pattern sampling inputs.

This does NOT establish which renderer is correct or prove Flash pixel parity.
Only mt_00/mt_01 are supported until their original source bindings are verified.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = '{http://www.w3.org/2000/svg}'
XLINK = '{http://www.w3.org/1999/xlink}'
ALIASES = ('mt_00', 'mt_01')
SHA = re.compile(r'[0-9a-f]{64}\Z')
PNG_SIG = b'\x89PNG\r\n\x1a\n'


def _style_value(node, name):
    if name in node.attrib:
        return node.get(name)
    for decl in node.get('style', '').split(';'):
        if ':' in decl:
            key, value = decl.split(':', 1)
            if key.strip() == name:
                return value.strip()
    return None


def _png_header(blob):
    # IHDR is required to be the first PNG chunk; this is a header audit,
    # not a complete PNG decoder or a CRC check of all later chunks.
    if (len(blob) < 33 or not blob.startswith(PNG_SIG) or
            blob[8:12] != b'\x00\x00\x00\r' or blob[12:16] != b'IHDR'):
        raise ValueError('invalid embedded PNG IHDR')
    import zlib
    if (zlib.crc32(blob[12:29]) & 0xffffffff) != int.from_bytes(blob[29:33], 'big'):
        raise ValueError('embedded PNG IHDR CRC mismatch')
    width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', blob[16:29])
    if (width == 0 or height == 0 or width > 16384 or height > 16384 or
            depth not in (1, 2, 4, 8, 16) or color not in (0, 2, 3, 4, 6) or
            compression != 0 or filtering != 0 or interlace not in (0, 1)):
        raise ValueError('invalid embedded PNG dimensions or IHDR fields')
    return {'width': width, 'height': height, 'bit_depth': depth,
            'color_type': color, 'interlace': interlace}


def inspect_svg(svg_bytes):
    try:
        root = ET.fromstring(svg_bytes)
    except ET.ParseError as exc:
        raise ValueError('invalid source SVG') from exc
    if root.tag != SVG + 'svg':
        raise ValueError('unexpected SVG root')
    patterns, images = [], []
    for node in root.iter():
        if node.tag == SVG + 'pattern':
            patterns.append({
                'id': node.get('id'),
                **{key: node.get(key) for key in
                   ('x', 'y', 'width', 'height', 'patternUnits', 'patternContentUnits', 'patternTransform')},
                'image_rendering': _style_value(node, 'image-rendering'),
            })
        if node.tag != SVG + 'image':
            continue
        href = node.get('href', node.get(XLINK + 'href', ''))
        item = {key: node.get(key) for key in ('x', 'y', 'width', 'height', 'transform', 'preserveAspectRatio')}
        item['image_rendering'] = _style_value(node, 'image-rendering')
        if not href.startswith('data:'):
            # Do not fetch external URLs or claim these bytes are verified.
            item['source_kind'] = 'external_or_missing'
            item['reference'] = href[:128]
        else:
            header, separator, payload = href.partition(',')
            if not separator or ';base64' not in header.lower():
                raise ValueError('unsupported embedded image data URI')
            try:
                blob = base64.b64decode(re.sub(r'\s+', '', payload), validate=True)
            except (ValueError, base64.binascii.Error) as exc:
                raise ValueError('invalid embedded image base64') from exc
            if not blob or len(blob) > 16 * 1024 * 1024:
                raise ValueError('invalid embedded image byte size')
            item.update(source_kind='embedded', media_type=header[5:].split(';', 1)[0].lower(),
                        byte_count=len(blob), sha256=hashlib.sha256(blob).hexdigest())
            if item['media_type'] == 'image/png':
                item['png_ihdr'] = _png_header(blob)
        images.append(item)
    return {'pattern_count': len(patterns), 'image_count': len(images),
            'svg_image_rendering': _style_value(root, 'image-rendering'),
            'patterns': patterns, 'images': images}


def audit(manifest, registration, export_root):
    swf = manifest.get('original', {}).get('sha256')
    if (not isinstance(swf, str) or not SHA.fullmatch(swf) or
            registration.get('swf_sha256') != swf or
            registration.get('registration_verified_for_static_aliases') is not True or
            set(registration.get('verified_static_aliases', {})) != set(ALIASES)):
        raise ValueError('original SWF/registration provenance mismatch')
    inventory = {}
    for entry in manifest.get('files', []):
        path, digest = entry.get('path'), entry.get('sha256')
        if not isinstance(path, str) or path in inventory:
            raise ValueError('duplicate or invalid FFDec manifest entry')
        inventory[path] = digest
    root = Path(export_root).resolve()
    results = {}
    for alias in ALIASES:
        binding = registration['verified_static_aliases'][alias]
        cid = binding.get('shape_id')
        path = f'shapes/{cid}.svg'
        expected = binding.get('sha256')
        if (type(cid) is not int or cid <= 0 or binding.get('source') != path or
                not isinstance(expected, str) or not SHA.fullmatch(expected) or
                inventory.get(path) != expected):
            raise ValueError(f'original FFDec SVG binding mismatch: {alias}')
        source = (root / path).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            raise ValueError(f'missing source SVG: {alias}')
        data = source.read_bytes()
        if len(data) > 16 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'source SVG SHA256 mismatch: {alias}')
        results[alias] = {'shape_id': cid, 'svg_path': path,
                          'svg_sha256': expected, **inspect_svg(data)}
    return {'schema_version': 1, 'swf_sha256': swf,
            'purpose': 'FFDec SVG embedded bitmap and pattern sampling inventory',
            'sampling_root_cause_verified': False, 'flash_pixel_parity_verified': False,
            'gameplay_parity_verified': False, 'gymnasium_kaggle_started': False,
            'sprites': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('manifest', 'registration', 'export-root', 'out'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.manifest.read_text(encoding='utf-8')),
                       json.loads(args.registration.read_text(encoding='utf-8')),
                       args.export_root)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f'SVG sampling audit FAILED: {exc}\n')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    for alias, info in result['sprites'].items():
        print(f"{alias}: {info['pattern_count']} patterns, {info['image_count']} images")
    print('PASS: FFDec SVG sampling inventory source-verified; root cause and Flash parity NOT VERIFIED')


if __name__ == '__main__':
    main()
