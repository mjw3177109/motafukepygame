"""Verify raw Flash monster arrays and starting stats against pinned SWF evidence.

This does NOT infer combat formulas, monster-field meanings, or gameplay parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from tools.extract_original_tables import BASE, MONSTER

SOURCE_PATH = 'export/scripts/frame_4346/DoAction.as'
SHA256 = re.compile(r'[0-9a-f]{64}\Z')
MONSTER_IDS = {str(i) for i in range(33)}
BASE_NAMES = {'life', 'hp', 'gong', 'fang', 'money', 'yellow', 'blue', 'red', 'mp'}
GATES = ('combat_formula_verified', 'gameplay_parity_verified', 'gymnasium_ready', 'kaggle_started')


def _check_tables(tables: object, label: str) -> None:
    if not isinstance(tables, dict):
        raise ValueError(f'{label}: expected object')
    monsters = tables.get('monsters')
    stats = tables.get('base_stats')
    if not isinstance(monsters, dict) or set(monsters) != MONSTER_IDS:
        raise ValueError(f'{label}: expected original monster ids 0..32')
    if not isinstance(stats, dict) or set(stats) != BASE_NAMES:
        raise ValueError(f'{label}: expected all nine original base stats')
    for monster_id, row in monsters.items():
        if (not isinstance(row, list) or len(row) != 6 or
            any(type(v) is not int for v in row[:5]) or
            not isinstance(row[5], str) or not row[5]):
            raise ValueError(f'{label}: invalid raw monster array at {monster_id}')
    if any(type(v) is not int for v in stats.values()):
        raise ValueError(f'{label}: noninteger base stat')


def _parse_raw_combat_source(script_bytes: bytes) -> tuple[dict, dict]:
    """Re-read original ActionScript, never trust a matching pair of JSON files."""
    source = script_bytes.decode('utf-8-sig')
    monsters = {}
    for fields in MONSTER.findall(source):
        monster_id = str(int(fields[0]))
        if monster_id in monsters:
            raise ValueError(f'duplicate original ActionScript monster {monster_id}')
        monsters[monster_id] = [int(v) for v in fields[1:6]] + [fields[6]]
    if set(monsters) != MONSTER_IDS:
        raise ValueError('original ActionScript monster declarations incomplete')
    stats = {}
    for name, raw in BASE.findall(source):
        if name in stats:
            raise ValueError(f'duplicate original ActionScript base stat {name}')
        stats[name] = int(raw)
    if set(stats) != BASE_NAMES:
        raise ValueError('original ActionScript base stats incomplete')
    return monsters, stats


def verify_original_combat_tables(committed: dict, extracted: dict,
                                  floor_anchors: dict, export_root: Path, swf_path: Path) -> dict:
    """Compare each raw value to independent pinned source and exported bytes."""
    if not all(isinstance(x, dict) for x in (committed, extracted, floor_anchors)):
        raise ValueError('expected three JSON objects')
    if any(x.get('schema_version') != 1 for x in (committed, extracted, floor_anchors)):
        raise ValueError('unsupported original table schema')
    pinned = floor_anchors.get('source')
    source = committed.get('source')
    actual = extracted.get('source')
    if not all(isinstance(x, dict) for x in (pinned, source, actual)):
        raise ValueError('missing independent source anchors')
    for key in ('swf_sha256', 'actionscript_sha256'):
        value = source.get(key)
        if not isinstance(value, str) or not SHA256.fullmatch(value):
            raise ValueError(f'invalid source {key}')
        if value != pinned.get(key) or value != actual.get(key):
            raise ValueError(f'original {key} anchor mismatch')
    if any(x.get('actionscript_path') != SOURCE_PATH for x in (source, actual, pinned)):
        raise ValueError('original ActionScript path mismatch')
    if not swf_path.is_file():
        raise ValueError('missing original SWF')
    if hashlib.sha256(swf_path.read_bytes()).hexdigest() != source['swf_sha256']:
        raise ValueError('original SWF bytes hash mismatch')
    script_path = Path(export_root).resolve() / SOURCE_PATH
    if not script_path.is_file() or not script_path.resolve().is_relative_to(Path(export_root).resolve()):
        raise ValueError('missing or unsafe original ActionScript export')
    if hashlib.sha256(script_path.read_bytes()).hexdigest() != source['actionscript_sha256']:
        raise ValueError('original ActionScript export hash mismatch')
    if committed.get('monster_field_order') != extracted.get('monster_field_order') or not isinstance(committed.get('monster_field_order'), str):
        raise ValueError('raw monster field order provenance mismatch')
    for gate in GATES:
        if committed.get(gate) is not False:
            raise ValueError(f'unsafe or missing acceptance gate: {gate}')
    _check_tables(committed, 'committed')
    _check_tables(extracted, 'FFDec')
    for monster_id in sorted(MONSTER_IDS, key=int):
        for field_index, (a, b) in enumerate(zip(committed['monsters'][monster_id], extracted['monsters'][monster_id])):
            if a != b:
                raise ValueError(f'original monster drift at {monster_id}[{field_index}]: committed={a!r}, FFDec={b!r}')
    for key in sorted(BASE_NAMES):
        if committed['base_stats'][key] != extracted['base_stats'][key]:
            raise ValueError(f'original base stat drift at {key}: committed={committed["base_stats"][key]}, FFDec={extracted["base_stats"][key]}')
    # Both JSON copies can agree while diverging from the unchanged original script.
    source_monsters, source_stats = _parse_raw_combat_source(script_path.read_bytes())
    for monster_id in sorted(MONSTER_IDS, key=int):
        for field_index, (value, raw_value) in enumerate(zip(extracted['monsters'][monster_id], source_monsters[monster_id])):
            if value != raw_value:
                raise ValueError(f'ActionScript monster drift at {monster_id}[{field_index}]')
    for key in sorted(BASE_NAMES):
        if extracted['base_stats'][key] != source_stats[key]:
            raise ValueError(f'ActionScript base stat drift at {key}')
    return {'schema_version': 1, 'swf_sha256': source['swf_sha256'],
            'monster_count': 33, 'raw_fields_per_monster': 6, 'base_stat_count': 9,
            'raw_source_verified': True, 'combat_formula_verified': False,
            'gameplay_parity_verified': False, 'gymnasium_ready': False, 'kaggle_started': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('committed', 'extracted', 'floor-anchors', 'export-root', 'swf', 'out'):
        parser.add_argument('--' + arg, required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify_original_combat_tables(
            json.loads(args.committed.read_text(encoding='utf-8')),
            json.loads(args.extracted.read_text(encoding='utf-8')),
            json.loads(args.floor_anchors.read_text(encoding='utf-8')), args.export_root, args.swf)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError) as error:
        parser.exit(2, f'FAIL: original raw combat tables: {error}\n')
    print('PASS: 33 original monster arrays and 9 base stats match hashed ActionScript; combat formulas NOT VERIFIED')


if __name__ == '__main__':
    main()
