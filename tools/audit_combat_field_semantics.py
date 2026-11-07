"""Fail-closed source audit of Flash monster fields and encounter gate.

Only static ActionScript semantics are established. This is not a live Flash
replay, complete battle engine, or permission to begin Gymnasium/Kaggle work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

RENDERER_PATH = 'export/scripts/frame_4346/DoAction_2.as'
FIELD_USES = {
    'monster_hp': ('_root.mt_kills.left_hp', '=', 0),
    'monster_attack': ('_root.mt_kills.left_gong', '=', 1),
    'monster_defense': ('_root.mt_kills.left_fang', '=', 2),
    'gold_reward': ('_root.Now_money', '+=', 3),
    'experience_reward': ('_root.Now_mp', '+=', 4),
}
GATE_EXPRESSION = ('tmp_kills=int(_root.boss_man[tmp_boss][0]/'
                   '(_root.Now_gong-_root.boss_man[tmp_boss][2]))*'
                   '(_root.boss_man[tmp_boss][1]-_root.Now_fang);')
SPECIAL_BONUSES = {
    20: '100', 12: '300',
    10: 'int(_root.Now_hp/4)', 17: 'int(_root.Now_hp/3)',
}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _compact(text: str) -> str:
    return re.sub(r'\s+', '', text)


def audit_combat_field_semantics(script: bytes, swf: bytes, floors: dict,
                                 combat: dict) -> dict:
    """Require independent source hashes, exact field uses and gate branches."""
    if not isinstance(floors, dict) or not isinstance(combat, dict):
        raise ValueError('missing original source anchors')
    fs, cs = floors.get('source'), combat.get('source')
    if not isinstance(fs, dict) or not isinstance(cs, dict):
        raise ValueError('missing original source anchors')
    if fs.get('renderer_actionscript_path') != RENDERER_PATH:
        raise ValueError('unexpected original renderer script path')
    if _digest(swf) != fs.get('swf_sha256') or cs.get('swf_sha256') != fs.get('swf_sha256'):
        raise ValueError('original SWF hash mismatch')
    if _digest(script) != fs.get('renderer_actionscript_sha256'):
        raise ValueError('original renderer ActionScript hash mismatch')
    source = script.decode('utf-8-sig')
    roles = {}
    for role, (target, operator, expected) in FIELD_USES.items():
        pattern = (re.escape(target) + r'\s*' + re.escape(operator) +
                   r'\s*_root\.boss_man\[_root\.Now_boss_id\]\[(\d+)\]\s*;')
        matches = re.findall(pattern, source)
        if matches != [str(expected)]:
            raise ValueError(f'original monster field mapping mismatch: {role}')
        roles[role] = expected
    compact = _compact(source)
    if compact.count(GATE_EXPRESSION) != 1:
        raise ValueError('original encounter loss expression mismatch')
    if compact.count('if(_root.boss_man[tmp_boss][2]>=_root.Now_gong)') != 1:
        raise ValueError('original attack-versus-defense entry gate mismatch')
    if compact.count('elseif(tmp_kills>_root.Now_hp)') != 1:
        raise ValueError('original HP entry gate mismatch')
    switches = re.findall(r'switch\s*\(\s*tmp_boss\s*\)\s*\{(.*?)\}', source, re.S)
    if len(switches) != 1:
        raise ValueError('original monster special switch missing or ambiguous')
    found = re.findall(r'case\s+(\d+)\s*:\s*tmp_kills\s*\+=\s*([^;]+);', switches[0])
    bonuses = {int(number): _compact(value) for number, value in found}
    if len(found) != len(bonuses) or bonuses != SPECIAL_BONUSES:
        raise ValueError('original monster special-loss branch mismatch')
    return {
        'schema_version': 1, 'swf_sha256': _digest(swf),
        'renderer_actionscript_sha256': _digest(script),
        'field_roles': roles, 'special_entry_bonuses': {str(k): v for k, v in SPECIAL_BONUSES.items()},
        'field_semantics_source_verified': True, 'encounter_gate_source_verified': True,
        'full_battle_verified': False, 'flash_replay_verified': False,
        'gameplay_parity_verified': False, 'gymnasium_ready': False, 'kaggle_started': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('script', 'swf', 'floors', 'combat', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit_combat_field_semantics(
            args.script.read_bytes(), args.swf.read_bytes(),
            json.loads(args.floors.read_text(encoding='utf-8')),
            json.loads(args.combat.read_text(encoding='utf-8')))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f'FAIL: original combat source semantics: {exc}\n')
    print('PASS: original five monster field roles and encounter gate branches match pinned ActionScript; full battle NOT VERIFIED')


if __name__ == '__main__':
    main()
