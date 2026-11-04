"""Evidence-only SWF PlaceObject2 snapshots for every original mt_* sprite.

No SVG registration, bitmap rendering, ActionScript execution or pixel parity is inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

TAG = re.compile(r'^([0-9a-fA-F]{8}):(\s+)(\d+)\.\s+(.*?)\s+tagId=\s*(\d+)\s+len=\s*(\d+)\s*(.*)$')
CHAR = re.compile(r'\((\d+)\)')
DEPTH = re.compile(r'Depth:\s*(\d+)')
HEX = re.compile(r'[0-9a-fA-F]{2}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')


class Bits:
    def __init__(self, data: bytes):
        self.data, self.pos = data, 0

    def read(self, n: int, signed: bool = False) -> int:
        if n < 0 or self.pos + n > len(self.data) * 8:
            raise ValueError('truncated MATRIX bit field')
        result = 0
        for _ in range(n):
            result = (result << 1) | ((self.data[self.pos // 8] >> (7 - self.pos % 8)) & 1)
            self.pos += 1
        if signed and n and result & (1 << (n - 1)):
            result -= 1 << n
        return result

    def align(self) -> int:
        self.pos = (self.pos + 7) // 8 * 8
        return self.pos // 8


def matrix(data: bytes) -> tuple[dict, int]:
    bits = Bits(data)
    a = d = 65536
    b = c = 0
    if bits.read(1):
        n = bits.read(5)
        a, d = bits.read(n, True), bits.read(n, True)
    if bits.read(1):
        n = bits.read(5)
        b, c = bits.read(n, True), bits.read(n, True)
    n = bits.read(5)
    tx, ty = bits.read(n, True), bits.read(n, True)
    return {'a_fixed16': a, 'b_fixed16': b, 'c_fixed16': c, 'd_fixed16': d,
            'tx_twips': tx, 'ty_twips': ty}, bits.align()


def payload_bytes(raw: str, length: int) -> bytes:
    tokens = raw.split()
    if len(tokens) != length or not all(HEX.fullmatch(token) for token in tokens):
        raise ValueError('truncated or nonhex FFDec tag payload')
    return bytes(int(token, 16) for token in tokens)


def placement(data: bytes, previous: dict | None) -> tuple[int, dict]:
    if len(data) < 3:
        raise ValueError('truncated PlaceObject2')
    flags, depth = data[0], int.from_bytes(data[1:3], 'little')
    if not depth or flags & 0xB8:
        raise ValueError('unsupported PlaceObject2 flags/depth')
    moving, has_character, has_matrix, has_clip = bool(flags & 1), bool(flags & 2), bool(flags & 4), bool(flags & 0x40)
    if moving != (previous is not None):
        raise ValueError('PlaceObject2 depth lifecycle mismatch')
    if not moving and not has_character:
        raise ValueError('new PlaceObject2 lacks character')
    pos = 3
    char_id = previous['character_id'] if previous else None
    if has_character:
        if len(data) < pos + 2:
            raise ValueError('truncated PlaceObject2 character')
        char_id = int.from_bytes(data[pos:pos + 2], 'little')
        pos += 2
    if not char_id:
        raise ValueError('invalid PlaceObject2 character')
    transform = previous['matrix'] if previous else None
    if has_matrix:
        transform, used = matrix(data[pos:])
        pos += used
    if transform is None:
        raise ValueError('PlaceObject2 lacks MATRIX')
    clip = previous['clip_depth'] if previous else None
    if has_clip:
        if len(data) < pos + 2:
            raise ValueError('truncated PlaceObject2 clip depth')
        clip = int.from_bytes(data[pos:pos + 2], 'little')
        pos += 2
        if clip <= depth:
            raise ValueError('invalid PlaceObject2 clip depth')
    if pos != len(data):
        raise ValueError('unexpected PlaceObject2 trailing bytes')
    return depth, {'character_id': char_id, 'matrix': transform, 'clip_depth': clip}


def frame_label(data: bytes) -> str:
    """Decode the null-terminated SWF FrameLabel string; reject anchor/trailing bytes."""
    if not data or data[-1] != 0 or 0 in data[:-1]:
        raise ValueError('invalid FrameLabel string')
    try:
        value = data[:-1].decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('invalid FrameLabel encoding') from exc
    if not value:
        raise ValueError('empty FrameLabel')
    return value


def snapshots(tag_text: str, character_id: int, offset: str, expected_frames: int) -> dict:
    active, found, state, frames, pending_actions, pending_labels = False, False, {}, [], [], []
    for line in tag_text.splitlines():
        match = TAG.match(line)
        if not match:
            continue
        at, spaces, _, label, tag_id, length, raw = match.groups()
        tag_id, length = int(tag_id), int(length)
        if len(spaces) <= 4:
            active = False
            if tag_id == 39 and CHAR.search(label) and int(CHAR.search(label).group(1)) == character_id:
                if found or at != offset:
                    raise ValueError('duplicate or relocated DefineSprite')
                header = payload_bytes(' '.join(raw.split()[:4]), 4)
                if int.from_bytes(header[:2], 'little') != character_id or int.from_bytes(header[2:4], 'little') != expected_frames:
                    raise ValueError('DefineSprite header/frame mismatch')
                found, active = True, True
            continue
        if not active:
            continue
        if tag_id == 26:
            data = payload_bytes(raw, length)
            depth_hint = DEPTH.search(label)
            if depth_hint is None:
                raise ValueError('missing PlaceObject2 depth label')
            depth = int.from_bytes(data[1:3], 'little')
            if depth != int(depth_hint.group(1)):
                raise ValueError('PlaceObject2 depth label mismatch')
            new_depth, item = placement(data, state.get(depth))
            character_hint = CHAR.search(label)
            if character_hint and item['character_id'] != int(character_hint.group(1)):
                raise ValueError('PlaceObject2 character label mismatch')
            state[new_depth] = item
        elif tag_id == 28:
            data = payload_bytes(raw, length)
            if len(data) != 2:
                raise ValueError('invalid RemoveObject2 length')
            depth = int.from_bytes(data, 'little')
            if depth not in state:
                raise ValueError('RemoveObject2 unknown depth')
            del state[depth]
        elif tag_id == 12:
            pending_actions.append(at)
        elif tag_id == 43:
            pending_labels.append(frame_label(payload_bytes(raw, length)))
        elif tag_id == 1:
            if length:
                raise ValueError('nonempty ShowFrame')
            frame = {'frame': len(frames) + 1,
                     'placements': [{'depth': depth, **state[depth]} for depth in sorted(state)],
                     'uninterpreted_action_offsets': pending_actions}
            if pending_labels:
                frame['labels'] = pending_labels
            frames.append(frame)
            pending_actions, pending_labels = [], []
        elif tag_id not in (45,):
            raise ValueError(f'unsupported nested sprite tag {tag_id}')
    if not found or len(frames) != expected_frames or pending_actions or pending_labels:
        raise ValueError('missing sprite or incomplete timeline')
    digest = hashlib.sha256(json.dumps(frames, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'character_id': character_id, 'frame_count': len(frames),
            'timeline_sha256': digest, 'frames': frames,
            'uninterpreted_action_count': sum(len(frame['uninterpreted_action_offsets']) for frame in frames)}


def audit(tag_text: str, trace: dict, frame_report: dict, anchors: dict | None = None) -> dict:
    digest = hashlib.sha256(tag_text.encode()).hexdigest()
    if (trace.get('schema_version') != 1 or frame_report.get('schema_version') != 1 or
            trace.get('ffdec_tag_dump_sha256') != digest or
            frame_report.get('ffdec_tag_dump_sha256') != digest or
            trace.get('swf_sha256') != frame_report.get('swf_sha256')):
        raise ValueError('source provenance mismatch')
    symbols, frame_symbols = trace.get('symbols'), frame_report.get('sprites')
    if (not isinstance(symbols, dict) or not symbols or not isinstance(frame_symbols, dict) or
            set(symbols) != set(frame_symbols) or
            trace.get('resolved_symbol_count') != len(symbols) or
            frame_report.get('verified_symbol_count') != len(symbols) or
            frame_report.get('frame_count_verified') is not True):
        raise ValueError('incomplete traced sprite/frame coverage')
    if anchors is not None:
        if not isinstance(anchors, dict):
            raise ValueError('placement anchors provenance mismatch')
        timelines = anchors.get('timelines')
        if (anchors.get('schema_version') != 1 or anchors.get('swf_sha256') != trace.get('swf_sha256') or
                not isinstance(timelines, dict) or set(timelines) != set(symbols) or
                any(not isinstance(value, str) or not SHA.fullmatch(value) for value in timelines.values())):
            raise ValueError('placement anchors provenance mismatch')
    results = {}
    for alias in sorted(symbols):
        symbol, frame = symbols[alias], frame_symbols[alias]
        if (not isinstance(symbol, dict) or not isinstance(frame, dict) or
                symbol.get('character_id') != frame.get('character_id') or
                symbol.get('define_offset') != frame.get('define_offset') or
                type(frame.get('frame_count')) is not int or frame['frame_count'] < 1):
            raise ValueError(f'missing trace/frame evidence: {alias}')
        result = snapshots(tag_text, symbol['character_id'], symbol['define_offset'], frame['frame_count'])
        if anchors is not None and anchors['timelines'][alias] != result['timeline_sha256']:
            raise ValueError(f'original placement timeline drift: {alias}')
        results[alias] = result
    action_count = sum(item['uninterpreted_action_count'] for item in results.values())
    labelled_frame_count = sum('labels' in frame for item in results.values() for frame in item['frames'])
    return {'schema_version': 1, 'swf_sha256': trace['swf_sha256'], 'ffdec_tag_dump_sha256': digest,
            'verified_aliases': sorted(results), 'verified_alias_count': len(results),
            'total_frame_snapshots': sum(item['frame_count'] for item in results.values()),
            'uninterpreted_action_count': action_count, 'labelled_frame_count': labelled_frame_count,
            'sprites': results, 'matrix_source_verified': True, 'actionscript_executed': False,
            'registration_verified': False, 'visual_parity_verified': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('tags', 'trace', 'frames', 'out'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--anchors', type=Path)
    args = parser.parse_args()
    try:
        load = lambda file: json.loads(file.read_text(encoding='utf-8'))
        result = audit(args.tags.read_text(encoding='utf-8'), load(args.trace), load(args.frames),
                       load(args.anchors) if args.anchors else None)
    except (ValueError, KeyError, TypeError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f'Sprite placement audit FAILED: {exc}\n')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"PASS: {result['verified_alias_count']} source sprite placement timelines, "
          f"{result['total_frame_snapshots']} frame snapshots, "
          f"{result['labelled_frame_count']} labelled frames; "
          'ActionScript, registration and visual parity NOT VERIFIED')


if __name__ == '__main__':
    main()
