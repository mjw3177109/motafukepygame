"""Verify FFDec DefineSprite declared frames against nested ShowFrame tags.

This proves only source timeline frame counts, not FPS, frame rendering,
registration, animation equivalence or pixel parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from tools.trace_swf_symbols import TAG, CHARACTER, HEXBYTE, SHA


def parse_sprite_frame_counts(tag_text: str) -> dict[int, dict]:
    """Extract source frame counts without guessing from exported image files."""
    definitions = {}
    active = None
    for line in tag_text.splitlines():
        match = TAG.match(line)
        if not match:
            continue
        offset, spaces, _, label, tag_id, length, payload = match.groups()
        tag_id, length, indent = int(tag_id), int(length), len(spaces)
        if indent <= 4:
            active = None
            if tag_id != 39:
                continue
            identifier = CHARACTER.search(label)
            if identifier is None or length < 4:
                raise ValueError('malformed DefineSprite header')
            character_id = int(identifier.group(1))
            tokens = payload.split()
            if len(tokens) < 4 or not all(HEXBYTE.fullmatch(token) for token in tokens[:4]):
                raise ValueError(f'truncated DefineSprite header {character_id}')
            header = bytes(int(token, 16) for token in tokens[:4])
            if int.from_bytes(header[:2], 'little') != character_id:
                raise ValueError(f'DefineSprite character ID mismatch {character_id}')
            declared = int.from_bytes(header[2:4], 'little')
            if declared < 1 or character_id in definitions:
                raise ValueError(f'invalid or duplicate DefineSprite {character_id}')
            definitions[character_id] = {'define_offset': offset, 'declared_frames': declared,
                                         'observed_showframes': 0}
            active = character_id
        elif active is not None and indent > 4 and tag_id == 1:
            if length != 0:
                raise ValueError(f'nonempty ShowFrame in sprite {active}')
            definitions[active]['observed_showframes'] += 1
    return definitions


def audit_sprite_frames(tag_text: str, symbol_trace: dict, anchors: dict | None = None) -> dict:
    if not isinstance(symbol_trace, dict) or symbol_trace.get('schema_version') != 1:
        raise ValueError('invalid symbol trace schema')
    digest = hashlib.sha256(tag_text.encode('utf-8')).hexdigest()
    if symbol_trace.get('ffdec_tag_dump_sha256') != digest:
        raise ValueError('FFDec tag dump SHA256 mismatch')
    swf_sha = symbol_trace.get('swf_sha256')
    if not isinstance(swf_sha, str) or not SHA.fullmatch(swf_sha):
        raise ValueError('invalid source SWF SHA256')
    symbols = symbol_trace.get('symbols')
    if not isinstance(symbols, dict) or not symbols or len(symbols) != symbol_trace.get('resolved_symbol_count'):
        raise ValueError('invalid symbol trace coverage')
    if anchors is not None:
        if (not isinstance(anchors, dict) or anchors.get('schema_version') != 1 or
                anchors.get('swf_sha256') != swf_sha or not isinstance(anchors.get('anchors'), dict)):
            raise ValueError('sprite frame anchors provenance mismatch')
        if set(anchors['anchors']) - set(symbols):
            raise ValueError('unknown sprite frame anchor')
    definitions = parse_sprite_frame_counts(tag_text)
    result = {}
    for alias in sorted(symbols):
        item = symbols[alias]
        if not isinstance(item, dict) or type(item.get('character_id')) is not int:
            raise ValueError(f'invalid traced sprite {alias}')
        character_id = item['character_id']
        frame = definitions.get(character_id)
        if frame is None or frame['define_offset'] != item.get('define_offset'):
            raise ValueError(f'missing or mismatched DefineSprite for {alias}')
        if frame['declared_frames'] != frame['observed_showframes']:
            raise ValueError(f'ShowFrame count mismatch for {alias}: '
                             f"declared {frame['declared_frames']}, observed {frame['observed_showframes']}")
        if anchors is not None and alias in anchors['anchors']:
            expected = anchors['anchors'][alias]
            if expected != {'character_id': character_id, 'frame_count': frame['declared_frames']}:
                raise ValueError(f'original frame anchor drift: {alias}')
        result[alias] = {'character_id': character_id, 'define_offset': frame['define_offset'],
                         'frame_count': frame['declared_frames'],
                         'showframe_count': frame['observed_showframes']}
    histogram = Counter(item['frame_count'] for item in result.values())
    return {'schema_version': 1, 'swf_sha256': swf_sha, 'ffdec_tag_dump_sha256': digest,
            'verified_symbol_count': len(result),
            'frame_count_histogram': {str(k): histogram[k] for k in sorted(histogram)},
            'sprites': result, 'frame_count_verified': True,
            'frame_content_verified': False, 'registration_verified': False,
            'visual_parity_verified': False, 'gameplay_parity_verified': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tags', type=Path, required=True)
    parser.add_argument('--trace', type=Path, required=True)
    parser.add_argument('--anchors', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        load = lambda path: json.loads(path.read_text(encoding='utf-8'))
        report = audit_sprite_frames(args.tags.read_text(encoding='utf-8'), load(args.trace),
                                     load(args.anchors) if args.anchors else None)
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f'Original sprite frame audit FAILED: {exc}\n')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"PASS: {report['verified_symbol_count']} original sprite frame counts verified; "
          f"histogram={report['frame_count_histogram']}; frame content and visual parity NOT VERIFIED")


if __name__ == '__main__':
    main()
