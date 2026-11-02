"""Pin the source-only frame54 -> sprite855 -> Move_arrow(100) reward chain.

This does NOT prove Flash playback, death handling, or negative-HP gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SWF_SHA256 = '04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9'
COMPLETION_BLOCK_SHA256 = '8d799e14285dbb9b9205afe4c670ce7e08d1fb63d4a831d73de47547f2a99c05'
SOURCES = {
    'completion': ('scripts/DefineSprite_855/frame_1/DoAction.as',
                   'fdc32d3bc0ab4e511aade04b38a8b336030c33096c7ce3f4d14b58f5f9b1f0a6'),
    'reward': ('scripts/frame_4346/DoAction_2.as',
               '0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034'),
}


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _block(source: str, condition: str) -> str:
    """Extract a unique brace-delimited if body; reject missing/ambiguous anchors."""
    matches = list(re.finditer(r'\bif\s*\(\s*' + condition + r'\s*\)\s*\{', source))
    if len(matches) != 1:
        raise ValueError(f'expected one source block for {condition}')
    start = matches[0].end()
    depth = 1
    for i in range(start, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                return source[start:i]
    raise ValueError(f'unterminated source block for {condition}')


def audit_completion(scripts: dict[str, bytes], swf_sha256: str) -> dict:
    if swf_sha256 != SWF_SHA256:
        raise ValueError('original game.swf SHA256 mismatch')
    if set(scripts) != set(SOURCES):
        raise ValueError('expected exactly two original ActionScript sources')
    sources = []
    decoded = {}
    for name, (path, expected_sha) in SOURCES.items():
        raw = scripts[name]
        if not isinstance(raw, bytes) or (name == 'reward' and _hash(raw) != expected_sha):
            raise ValueError(f'{name} ActionScript byte SHA256 mismatch')
        decoded[name] = raw.decode('utf-8-sig')
        sources.append({'name': name, 'path': path, 'sha256': _hash(raw),
                        'full_byte_hash_pinned': name == 'reward',
                        'size_bytes': len(raw), 'source_verified': True})
    completion = _block(decoded['completion'], r'_root\.Display_kill\s*==\s*2')
    scoped_hash = _hash(completion.replace('\r\n', '\n').encode('utf-8'))
    if scoped_hash != COMPLETION_BLOCK_SHA256:
        raise ValueError('completion source block SHA256 mismatch')
    required = [r'_root\.DelMovie\("mt_kills"\)\s*;',
                r'_root\.DelMovie\("mt_kills_left"\)\s*;',
                r'_root\.DelMovie\("mt_kills_right"\)\s*;',
                r'_root\.Display_kill\s*=\s*0\s*;',
                r'_root\.Move_arrow\(100\)\s*;']
    positions = []
    for clause in required:
        match = re.search(clause, completion)
        if match is None:
            raise ValueError(f'completion clause missing: {clause}')
        positions.append(match.start())
    if positions != sorted(positions):
        raise ValueError('completion cleanup/dispatch order changed')
    reward = _block(decoded['reward'], r'arrow_id\s*==\s*100')
    for clause in (r'_root\.Display_text\s*=\s*1\s*;',
                   r'_root\.Now_money\s*\+=\s*_root\.boss_man\[_root\.Now_boss_id\]\[3\]\s*;',
                   r'_root\.Now_mp\s*\+=\s*_root\.boss_man\[_root\.Now_boss_id\]\[4\]\s*;',
                   r'_root\.mt_Mylife\.My_hp\s*=\s*_root\.Now_hp\s*;'):
        if re.search(clause, reward) is None:
            raise ValueError(f'reward clause missing: {clause}')
    for name, block in (('completion', completion), ('reward', reward)):
        if re.search(r'\bif\s*\([^)]*(?:Now_hp|right_hp)', block):
            raise ValueError(f'{name} contains a hero-HP conditional; re-audit required')
    return {
        'schema_version': 1, 'swf_sha256': SWF_SHA256, 'sources': sources,
        'source_chain': ['frame54: Display_kill=2, Now_hp=right_hp',
                         'sprite855 frame1: Display_kill==2 -> Move_arrow(100)',
                         'Move_arrow(100): clear monster, add money and MP'],
        'completion_scoped_sha256': scoped_hash,
        'completion_full_hash_may_drift_in_unrelated_ffdec_output': True,
        'no_hp_guard_in_these_two_blocks': True,
        'static_source_verified': True, 'flash_playback_verified': False,
        'global_death_handling_verified': False, 'negative_hp_runtime_verified': False,
        'gameplay_parity_verified': False, 'gymnasium_ready': False, 'kaggle_started': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-root', type=Path, required=True)
    parser.add_argument('--swf', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        scripts = {name: (args.export_root / path).read_bytes()
                   for name, (path, _) in SOURCES.items()}
        report = audit_completion(scripts, _hash(args.swf.read_bytes()))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        parser.exit(2, f'FAIL: original battle completion source audit: {exc}\n')
    print('PASS: source-scoped completion/reward chain; Flash death behavior NOT VERIFIED')


if __name__ == '__main__':
    main()
