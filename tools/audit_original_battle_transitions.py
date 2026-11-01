"""Pin original Flash battle frame 34/35/54 scripts (static evidence only).

The exported ActionScript is checked against independent byte and normalized
fingerprints. This cannot verify playback, death handling, or gameplay parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Mapping

SWF_SHA256 = '04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9'
SCRIPT_ROOT = 'export/scripts/DefineSprite_453_mt_other_04'
FRAMES = {
    34: {
        'sha256': '68fba28365be1e2a113611697ec24e3d96da3e9c3b08b3f6d96644744440972e',
        'compact_sha256': '7f128d72acd8defb0cd83fd692d03e4d4f0a164acefe9024d47515a86e5f911b',
        'clauses': {'loop': r'^if\(left_hp>0\)\{gotoAndPlay\(24\);\}$'},
    },
    35: {
        'sha256': '6e9dbc778499938292edc758151c4a5095cd0d1ac5361b0d2ebbe057d17b121c',
        'compact_sha256': '3298fa4bf3c7095794ee8a429454f6951f5d84ccde20945ed46c0a8d9afffa5b',
        'clauses': {'victory_sound': r'^_root\.PlaySound\("music_07"\);$'},
    },
    54: {
        'sha256': '112c9ad7454ad425124e1ccb6481ed71ddba58ad36ebc5dba6639a07f367893c',
        'compact_sha256': '8821c38710e59fa4a63628e2fe0f31dfacc32c7eb3c939647f3ec8487b0b5861',
        'clauses': {'handoff': r'^stop\(\);_root\.Display_kill=2;_root\.Now_hp=right_hp;$'},
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit_transitions(scripts: Mapping[int, bytes], swf_sha256: str) -> dict:
    """Fail closed if original SWF identity or any FFDec source differs."""
    if swf_sha256 != SWF_SHA256:
        raise ValueError('original game.swf SHA256 mismatch')
    if set(scripts) != set(FRAMES):
        raise ValueError('expected exactly frame 34, 35 and 54 ActionScript files')
    sources = []
    for frame, anchor in FRAMES.items():
        data = scripts[frame]
        if not isinstance(data, bytes) or sha256(data) != anchor['sha256']:
            raise ValueError(f'frame {frame} ActionScript SHA256 mismatch')
        try:
            source = data.decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise ValueError(f'frame {frame} is not UTF-8') from exc
        compact = re.sub(r'\s+', '', source)
        if sha256(compact.encode('utf-8')) != anchor['compact_sha256']:
            raise ValueError(f'frame {frame} normalized source mismatch')
        for label, pattern in anchor['clauses'].items():
            if re.fullmatch(pattern, compact) is None:
                raise ValueError(f'frame {frame} clause mismatch: {label}')
        sources.append({'frame': frame, 'path': f'{SCRIPT_ROOT}/frame_{frame}/DoAction.as',
                        'size_bytes': len(data), 'sha256': anchor['sha256'],
                        'source_verified': True})
    return {
        'schema_version': 1, 'swf_sha256': SWF_SHA256, 'sources': sources,
        'frame34_loop': 'if left_hp > 0, gotoAndPlay(24)',
        'frame35_sound': 'music_07',
        'frame54_handoff': ['stop()', 'Display_kill = 2', 'Now_hp = right_hp'],
        'static_source_verified': True,
        'flash_playback_verified': False, 'death_handling_verified': False,
        'full_battle_verified': False, 'gameplay_parity_verified': False,
        'gymnasium_ready': False, 'kaggle_started': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-root', type=Path, required=True,
                        help='FFDec export root, containing scripts/')
    parser.add_argument('--swf', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        scripts = {frame: (args.export_root / 'scripts' /
                            'DefineSprite_453_mt_other_04' / f'frame_{frame}' /
                            'DoAction.as').read_bytes() for frame in FRAMES}
        report = audit_transitions(scripts, sha256(args.swf.read_bytes()))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError) as exc:
        parser.exit(2, f'FAIL: original battle transitions audit: {exc}\n')
    print('PASS: original frame 34/35/54 static source pinned; Flash parity NOT VERIFIED')


if __name__ == '__main__':
    main()
