"""Fail closed when committed floor matrices drift from FFDec ActionScript extraction.

This checks static source provenance and all 3267 initial cells, not gameplay,
registration points, frame timing, or visual parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
FLOORS = {f"{i:02d}" for i in range(27)}


def _safe_export_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or "\\" in name or "\x00" in name:
        raise ValueError("unsafe exported ActionScript path")
    path = PurePosixPath(name)
    if path.is_absolute() or not name.startswith("export/scripts/") or any(
        segment in ("", ".", "..") for segment in name.split("/")
    ):
        raise ValueError("unsafe exported ActionScript path")
    base = root.resolve()
    target = (base / name).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        raise ValueError(f"missing or escaped exported ActionScript: {name}")
    return target


def _valid_floors(matrices: object, label: str) -> None:
    if not isinstance(matrices, dict) or set(matrices) != FLOORS:
        raise ValueError(f"{label}: expected exactly floors 00..26")
    for floor, matrix in matrices.items():
        if not isinstance(matrix, list) or len(matrix) != 11:
            raise ValueError(f"{label}: invalid 11-row matrix at {floor}")
        for row in matrix:
            if not isinstance(row, list) or len(row) != 11 or any(type(x) is not int for x in row):
                raise ValueError(f"{label}: invalid 11-column integer row at {floor}")


def verify_original_floors(committed: dict, extracted: dict, export_root: Path) -> dict:
    if not isinstance(committed, dict) or not isinstance(extracted, dict):
        raise ValueError("expected two JSON objects")
    if committed.get("schema_version") != 1 or extracted.get("schema_version") != 1:
        raise ValueError("unsupported table schema")
    source = committed.get("source")
    original = extracted.get("source")
    if not isinstance(source, dict) or not isinstance(original, dict):
        raise ValueError("missing source provenance")
    for key in ("swf_sha256", "actionscript_sha256"):
        if not isinstance(source.get(key), str) or not HEX64.fullmatch(source[key]):
            raise ValueError(f"invalid committed {key}")
        if source[key] != original.get(key):
            raise ValueError(f"source provenance differs: {key}")
    if source.get("actionscript_path") != original.get("actionscript_path"):
        raise ValueError("ActionScript source path differs")
    if "untransposed" not in str(committed.get("index_order", "")) or "untransposed" not in str(extracted.get("matrix_index_order", "")):
        raise ValueError("matrix index-order provenance is missing")
    script_fields = (
        (source["actionscript_path"], source["actionscript_sha256"]),
        (source.get("renderer_actionscript_path"), source.get("renderer_actionscript_sha256")),
    )
    for name, expected_sha in script_fields:
        if not isinstance(expected_sha, str) or not HEX64.fullmatch(expected_sha):
            raise ValueError("missing or invalid ActionScript digest")
        target = _safe_export_file(Path(export_root), name)
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected_sha:
            raise ValueError(f"exported ActionScript hash mismatch: {name}")
    _valid_floors(committed.get("floors"), "committed")
    _valid_floors(extracted.get("floors"), "extracted")
    for floor in sorted(FLOORS):
        for row in range(11):
            for column in range(11):
                a = committed["floors"][floor][row][column]
                b = extracted["floors"][floor][row][column]
                if a != b:
                    raise ValueError(
                        f"original floor drift at {floor}[{row}][{column}]: committed={a}, FFDec={b}"
                    )
    return {"floor_count": 27, "cell_count": 3267, "static_source_verified": True,
            "visual_parity_verified": False, "gameplay_parity_verified": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--committed", type=Path, required=True)
    parser.add_argument("--extracted", type=Path, required=True)
    parser.add_argument("--export-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_original_floors(
            json.loads(args.committed.read_text(encoding="utf-8")),
            json.loads(args.extracted.read_text(encoding="utf-8")), args.export_root)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(2, f"FAIL: original floor provenance verification: {error}\n")
    print(f"PASS: {result['floor_count']} floors, {result['cell_count']} static cells match hashed FFDec scripts; gameplay/visual parity NOT VERIFIED")


if __name__ == "__main__":
    main()
