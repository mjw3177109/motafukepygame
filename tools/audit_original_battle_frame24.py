"""Fail-closed byte/semantic audit of the original mt_other_04 frame-24 script.

This validates *static source evidence*, not Flash playback or battle parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SWF_SHA256 = '04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9'
SCRIPT_PATH = 'export/scripts/DefineSprite_453_mt_other_04/frame_24/DoAction.as'
SCRIPT_SHA256 = '98e293ed7fbfd1c0a6340c53a973fabf0a4c26f235467be6b1f3398469d24196'
COMPACT_SHA256 = '30401f98340722d9dde3f2a86ac353204217c8d97104a1248febf3a9c72d121a'

# Independent exact-source assertions; the full normalized fingerprint
# also detects extra statements or changed branching.
REQUIRED = {
    'active_guard': r'if\(left_hp>0\|\|right_hp>0\)',
    'hero_turn': r'if\(kill_number%2==0\)',
    'flash_roll': r'kill_max=random\(200\);',
    'inclusive_critical': r'if\(kill_max<=_root\.Now_life\)',
    'critical_damage': r'left_hp-=kill_right\*2;',
    'ordinary_damage': r'left_hp-=kill_right;',
    'monster_hp_clamp': r'if\(left_hp<0\)\{left_hp=0;\}',
    'monster_turn': r'if\(kill_number%2==1\)',
    'hero_hp_unclamped': r'right_hp-=kill_left;',
    'victory_transition': r'if\(left_hp==0\)\{gotoAndPlay\(35\);\}',
    'turn_increment': r'kill_number\+\+;',
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit_frame24(script: bytes, swf: bytes) -> dict:
    """Require original SWF, exact FFDec bytes, and the pinned semantics."""
    if _sha(swf) != SWF_SHA256:
        raise ValueError('original game.swf SHA256 mismatch')
    if _sha(script) != SCRIPT_SHA256:
        raise ValueError('original frame-24 ActionScript SHA256 mismatch')
    try:
        source = script.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('frame-24 ActionScript is not UTF-8') from exc
    compact = re.sub(r'\s+', '', source)
    if _sha(compact.encode('utf-8')) != COMPACT_SHA256:
        raise ValueError('frame-24 normalized source mismatch')
    for label, pattern in REQUIRED.items():
        if len(re.findall(pattern, compact)) != 1:
            raise ValueError(f'frame-24 original source clause mismatch: {label}')
    return {
        'schema_version': 1, 'source': SCRIPT_PATH,
        'swf_sha256': SWF_SHA256, 'actionscript_sha256': SCRIPT_SHA256,
        'frame24_source_verified': True,
        'critical_roll': 'Flash random(200), integers 0..199',
        'critical_comparison': 'roll <= Now_life (inclusive)',
        'critical_damage_multiplier': 2,
        'monster_counterattack_hp_clamped': False,
        'flash_replay_verified': False, 'full_battle_verified': False,
        'gameplay_parity_verified': False, 'gymnasium_ready': False,
        'kaggle_started': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('script', 'swf', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit_frame24(args.script.read_bytes(), args.swf.read_bytes())
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError) as exc:
        parser.exit(2, f'FAIL: original frame-24 source audit: {exc}\n')
    print('PASS: original mt_other_04 frame-24 clauses match pinned FFDec source; Flash parity NOT VERIFIED')


if __name__ == '__main__':
    main()
