"""Locate source-verified ending/dialogue event tile IDs in original static maps.

Static initial-cell locations are NOT proof of runtime event reachability.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.audit_terminal_guard_paths import audit_paths
from tools.verify_original_floors import verify_original_floors

# Locked against the original Flash 1.12 initial 27 x 11 x 11 maps.
# Indices retain mt_line_XX[outer_index][inner_index], not inferred x/y.
EXPECTED = {
    129: [("19", 7, 5)],
    24: [("00", 8, 5), ("22", 2, 6)],
}


def locate_tiles(floors: dict, guard: dict) -> dict:
    """Combine independently verified map matrices and event-source anchors."""
    if guard.get("source_anchors_verified") is not True or guard.get("source_manifest_verified") is not True:
        raise ValueError("terminal guard source was not verified")
    start = guard.get("say08_start_event", {})
    event = guard.get("tile_event", {})
    if (start.get("tile_id") != 129 or start.get("required_Display_say_8") != 0
            or start.get("assigned_Display_say_8") != 1
            or start.get("same_guarded_block_verified") is not True
            or event.get("tile_id") != 24 or event.get("mt_changes") != 1
            or event.get("my_love") != 0
            or event.get("assigned_mt_LastGame_ID") != 1
            or event.get("same_guarded_block_verified") is not True):
        raise ValueError("terminal event source guard differs from original anchors")
    if not isinstance(floors, dict) or set(floors) != {f"{i:02d}" for i in range(27)}:
        raise ValueError("expected all 27 original floor matrices")
    positions = {tile: [] for tile in EXPECTED}
    for floor in sorted(floors):
        matrix = floors[floor]
        if not isinstance(matrix, list) or len(matrix) != 11:
            raise ValueError(f"invalid original floor matrix {floor}")
        for outer, row in enumerate(matrix):
            if (not isinstance(row, list) or len(row) != 11
                    or any(type(value) is not int for value in row)):
                raise ValueError(f"invalid original floor row {floor}[{outer}]")
            for inner, tile in enumerate(row):
                if tile in positions:
                    positions[tile].append((floor, outer, inner))
    for tile, expected in EXPECTED.items():
        if positions[tile] != expected:
            raise ValueError(f"original tile {tile} locations differ: {positions[tile]}")
    return {
        "schema_version": 1,
        "matrix_index_order": "mt_line_XX[outer_index][inner_index] (untransposed)",
        "say08_start_tile": {
            "tile_id": 129,
            "locations": [dict(floor=f, outer_index=o, inner_index=i) for f, o, i in positions[129]],
            "requires_Display_say_8": 0,
            "sets_Display_say_8": 1,
        },
        "ending_guard_tile": {
            "tile_id": 24,
            "locations": [dict(floor=f, outer_index=o, inner_index=i) for f, o, i in positions[24]],
            "requires_mt_changes": 1,
            "requires_my_love": 0,
            "sets_mt_LastGame_ID": 1,
        },
        "initial_map_locations_source_verified": True,
        "runtime_event_reachability_verified": False,
        "dynamic_map_mutations_verified": False,
        "flash_ending_verified": False,
        "dual_client_parity_verified": False,
        "gymnasium_ready": False,
        "kaggle_started": False,
    }


def audit_locations(committed: dict, extracted: dict, manifest: dict,
                    export_root: Path, swf_bytes: bytes) -> dict:
    floor_proof = verify_original_floors(committed, extracted, export_root.parent)
    guard = audit_paths(manifest, export_root, swf_bytes)
    if guard["swf_sha256"] != committed["source"]["swf_sha256"]:
        raise ValueError("event and floor evidence refer to different original SWFs")
    report = locate_tiles(extracted["floors"], guard)
    report["swf_sha256"] = guard["swf_sha256"]
    report["actionscript_sha256"] = extracted["source"]["actionscript_sha256"]
    report["verified_static_cells"] = floor_proof["cell_count"]
    report["guard_source_paths"] = guard["sources"]
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--committed", type=Path, required=True)
    parser.add_argument("--extracted", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--swf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit_locations(
            json.loads(args.committed.read_text(encoding="utf-8")),
            json.loads(args.extracted.read_text(encoding="utf-8")),
            json.loads(args.manifest.read_text(encoding="utf-8")),
            args.export_root, args.swf.read_bytes(),
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"FAIL: terminal tile location audit: {exc}\n")
    print("PASS: source-verified initial tile 129 on floor 19 and tile 24 on floors 00/22; "
          "runtime reachability, ending and parity NOT VERIFIED")


if __name__ == "__main__":
    main()
