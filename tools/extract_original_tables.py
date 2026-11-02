"""Extract exact map/monster/base arrays from FFDec's original ActionScript.

This is a static data extractor, NOT a Flash interpreter.  It deliberately
preserves matrix index order and monster value order without guessing semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

FLOOR_DECL = re.compile(r"(?m)^mt_line_(\d{2})\s*=\s*new Array\((\d+)\);\s*$")
FLOOR_ROW = re.compile(r"(?m)^mt_line_(\d{2})\[(\d+)\]\s*=\s*new Array\(([^)]*)\);\s*$")
MONSTER = re.compile(r'(?m)^boss_man\[(\d+)\]\s*=\s*new Array\((\d+),(\d+),(\d+),(\d+),(\d+),"([^"\r\n]*)"\);\s*$')
BASE = re.compile(r"(?m)^Base_(life|hp|gong|fang|money|yellow|blue|red|mp)\s*=\s*(-?\d+);\s*$")


def parse_tables(script: bytes, *, swf_sha256: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{64}", swf_sha256):
        raise ValueError("source SWF SHA256 must be 64 lowercase hex characters")
    source = script.decode("utf-8-sig")
    declared = {}
    for floor, size in FLOOR_DECL.findall(source):
        if floor in declared:
            raise ValueError(f"duplicate floor declaration: {floor}")
        declared[floor] = int(size)
    expected_floors = [f"{i:02d}" for i in range(27)]
    if sorted(declared) != expected_floors or set(declared.values()) != {11}:
        raise ValueError("original floor declarations must be 00..26 with 11 outer entries")
    floors = {f: [None] * 11 for f in expected_floors}
    for floor, row_number, csv in FLOOR_ROW.findall(source):
        if floor not in floors:
            raise ValueError(f"undeclared floor {floor}")
        idx = int(row_number)
        if not 0 <= idx < 11 or floors[floor][idx] is not None:
            raise ValueError(f"duplicate or out-of-range row: {floor}[{idx}]")
        values = [value.strip() for value in csv.split(",")]
        if len(values) != 11 or any(not re.fullmatch(r"-?\d+", v) for v in values):
            raise ValueError(f"nonliteral or invalid 11-cell row: {floor}[{idx}]")
        floors[floor][idx] = [int(v) for v in values]
    if any(row is None for rows in floors.values() for row in rows):
        raise ValueError("missing floor rows")
    monsters = {}
    for fields in MONSTER.findall(source):
        idx = int(fields[0])
        if idx in monsters:
            raise ValueError(f"duplicate monster id {idx}")
        monsters[idx] = [int(v) for v in fields[1:6]] + [fields[6]]
    if sorted(monsters) != list(range(33)):
        raise ValueError("expected original monster ids 0..32")
    bases = {}
    for name, number in BASE.findall(source):
        if name in bases:
            raise ValueError(f"duplicate base stat {name}")
        bases[name] = int(number)
    if set(bases) != {"life", "hp", "gong", "fang", "money", "yellow", "blue", "red", "mp"}:
        raise ValueError("incomplete original base stats")
    return {
        "schema_version": 1,
        "source": {
            "swf_sha256": swf_sha256,
            "actionscript_path": "export/scripts/frame_4346/DoAction.as",
            "actionscript_sha256": hashlib.sha256(script).hexdigest(),
        },
        "matrix_index_order": "mt_line_XX[outer_index][inner_index] (untransposed)",
        "monster_field_order": "raw ActionScript array order; meanings require independent verification",
        "floors": floors,
        "monsters": {str(k): monsters[k] for k in sorted(monsters)},
        "base_stats": bases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--swf-sha256", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out", type=Path)
    group.add_argument("--verify", type=Path)
    args = parser.parse_args()
    actual = parse_tables(args.script.read_bytes(), swf_sha256=args.swf_sha256)
    if args.verify:
        expected = json.loads(args.verify.read_text(encoding="utf-8"))
        if actual != expected:
            parser.exit(1, "original ActionScript data differs from committed tables\n")
        print("PASS: 27 original 11x11 floors, 33 monsters, 9 base stats verified")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote original tables: {args.out}")


if __name__ == "__main__":
    main()
