"""Trace FFDec ExportAssets names to DefineSprite and hashed child SVGs.

This is SWF symbol provenance, NOT verified registration, animation or pixel parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TAG = re.compile(r'^([0-9a-fA-F]{8}):(\s+)(\d+)\.\s+(.*?)\s+tagId=\s*(\d+)\s+len=\s*(\d+)\s*(.*)$')
CHARACTER = re.compile(r'\((\d+)\)')
HEXBYTE = re.compile(r'[0-9a-fA-F]{2}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')


def _export_entries(payload, expected_length):
    tokens = payload.strip().split()
    if not all(HEXBYTE.fullmatch(token) for token in tokens):
        raise ValueError('truncated or malformed ExportAssets payload')
    raw = bytes(int(token, 16) for token in tokens)
    if len(raw) != expected_length or len(raw) < 2:
        raise ValueError('ExportAssets payload length differs from tag length')
    count = int.from_bytes(raw[:2], 'little')
    pos, entries = 2, []
    for _ in range(count):
        if pos + 2 > len(raw):
            raise ValueError('truncated ExportAssets character ID')
        character_id = int.from_bytes(raw[pos:pos + 2], 'little')
        pos += 2
        try:
            end = raw.index(0, pos)
        except ValueError as exc:
            raise ValueError('unterminated ExportAssets name') from exc
        name = raw[pos:end].decode('utf-8')
        if not name:
            raise ValueError('empty ExportAssets name')
        entries.append((name, character_id))
        pos = end + 1
    if pos != len(raw):
        raise ValueError('unexpected bytes after ExportAssets entries')
    return entries


def parse_tag_dump(tag_text):
    """Read only explicit FFDec tag lines; no guessed asset relationships."""
    exports, definitions, children = {}, {}, {}
    current_sprite = None
    for line in tag_text.splitlines():
        match = TAG.match(line)
        if not match:
            continue
        offset, spaces, _, label, tag, length, payload = match.groups()
        tag, length = int(tag), int(length)
        top_level = len(spaces) <= 4
        if top_level:
            current_sprite = None
        if top_level and tag == 56:
            for name, character_id in _export_entries(payload, length):
                existing = exports.setdefault(name, {'character_id': character_id, 'export_offsets': []})
                if existing['character_id'] != character_id:
                    raise ValueError(f'conflicting ExportAssets IDs for {name}')
                existing['export_offsets'].append(offset)
        elif top_level and tag in (2, 22, 32, 39):
            identifier = CHARACTER.search(label)
            if not identifier:
                raise ValueError('definition tag lacks character ID')
            character_id = int(identifier.group(1))
            if character_id in definitions:
                raise ValueError(f'duplicate definition ID {character_id}')
            definitions[character_id] = {'tag': tag, 'offset': offset}
            if tag == 39:
                current_sprite = character_id
                children[character_id] = []
        elif not top_level and current_sprite is not None and tag in (4, 26, 70):
            identifier = CHARACTER.search(label)
            if identifier:
                children[current_sprite].append(int(identifier.group(1)))
    return exports, definitions, children


def trace_symbols(tag_text, manifest, coverage, export_root, anchors=None):
    if not isinstance(manifest, dict) or not isinstance(coverage, dict):
        raise ValueError('missing FFDec manifest or asset coverage')
    swf_hash = manifest.get('original', {}).get('sha256')
    if not isinstance(swf_hash, str) or not SHA.fullmatch(swf_hash) or coverage.get('swf_sha256') != swf_hash:
        raise ValueError('SWF provenance mismatch')
    required = coverage.get('required_sources')
    if not isinstance(required, list) or not required or any(not isinstance(x, str) or not re.fullmatch(r'mt_\d+', x) for x in required) or len(required) != len(set(required)):
        raise ValueError('invalid required sprite aliases')
    files = manifest.get('files')
    if not isinstance(files, list):
        raise ValueError('invalid FFDec file inventory')
    inventory = {}
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get('path'), str) or not isinstance(entry.get('sha256'), str):
            raise ValueError('invalid FFDec inventory entry')
        if entry['path'] in inventory:
            raise ValueError('duplicate FFDec inventory path')
        inventory[entry['path']] = entry['sha256']
    exports, definitions, children = parse_tag_dump(tag_text)
    if anchors is not None:
        if anchors.get('swf_sha256') != swf_hash or anchors.get('schema_version') != 1 or not isinstance(anchors.get('anchors'), dict):
            raise ValueError('anchor SWF provenance mismatch')
    root = Path(export_root).resolve()
    verified = {}
    for alias in sorted(required):
        export = exports.get(alias)
        if not export:
            raise ValueError(f'original ExportAssets alias missing: {alias}')
        character_id = export['character_id']
        definition = definitions.get(character_id)
        if not definition or definition['tag'] != 39:
            raise ValueError(f'{alias} does not resolve to a DefineSprite')
        shape_ids = sorted(set(children.get(character_id, [])))
        if not shape_ids:
            raise ValueError(f'{alias} sprite has no explicitly placed shapes')
        shape_exports = []
        for shape_id in shape_ids:
            if definitions.get(shape_id, {}).get('tag') not in (2, 22, 32):
                raise ValueError(f'{alias} has non-shape child {shape_id}; manual inspection required')
            path = f'shapes/{shape_id}.svg'
            digest = inventory.get(path)
            if not isinstance(digest, str) or not SHA.fullmatch(digest):
                raise ValueError(f'{alias} shape absent from hashed FFDec inventory: {path}')
            target = (root / path).resolve()
            if not target.is_relative_to(root) or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError(f'{alias} shape bytes do not match FFDec inventory: {path}')
            shape_exports.append({'character_id': shape_id, 'path': path, 'sha256': digest})
        if anchors is not None and alias in anchors['anchors']:
            expected = anchors['anchors'][alias]
            if expected != {'character_id': character_id, 'shape_ids': shape_ids}:
                raise ValueError(f'original symbol anchor drift: {alias}')
        verified[alias] = {'character_id': character_id, 'define_offset': definition['offset'],
                           'export_offsets': export['export_offsets'], 'shape_exports': shape_exports}
    if anchors is not None and set(anchors['anchors']) - set(verified):
        raise ValueError('anchor alias not required by current floor layout')
    return {'schema_version': 1, 'swf_sha256': swf_hash,
            'ffdec_tag_dump_sha256': hashlib.sha256(tag_text.encode('utf-8')).hexdigest(),
            'required_alias_count': len(required), 'resolved_symbol_count': len(verified),
            'unique_shape_count': len({s['character_id'] for v in verified.values() for s in v['shape_exports']}),
            'symbols': verified, 'registration_verified': False,
            'visual_parity_verified': False, 'gameplay_parity_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tags', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--coverage', type=Path, required=True)
    parser.add_argument('--export-root', type=Path, required=True)
    parser.add_argument('--anchors', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        read_json = lambda path: json.loads(path.read_text(encoding='utf-8'))
        report = trace_symbols(args.tags.read_text(encoding='utf-8'), read_json(args.manifest),
                               read_json(args.coverage), args.export_root,
                               read_json(args.anchors) if args.anchors else None)
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f'Original SWF symbol trace FAILED: {exc}\n')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"PASS: {report['resolved_symbol_count']}/{report['required_alias_count']} "
          f"ExportAssets-to-DefineSprite symbols; {report['unique_shape_count']} hashed SVG shapes; "
          'registration and visual parity NOT VERIFIED')


if __name__ == '__main__':
    main()
