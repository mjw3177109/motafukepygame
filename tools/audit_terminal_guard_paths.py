"""Fail-closed static evidence for mt_LastGame_ID event and save/load paths.

Checks source bytes against the FFDec manifest and original SWF via the shared
provenance audit. This is NOT an ActionScript interpreter or Flash parity test.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Callable

from tools.audit_terminal_candidates import audit_candidates, sha256

INIT = "scripts/frame_4346/DoAction.as"
CONTROL = "scripts/frame_4346/DoAction_2.as"

EVENT = (
    r'if\s*\(\s*Number\(eval\(temp_lines\)\[temp_x\]\[temp_y\]\)\s*==\s*24'
    r'\s*&&\s*_root\.mt_changes\s*==\s*1\s*&&\s*_root\.my_love\s*==\s*0\s*\)\s*\{'
    r'\s*_root\.Now_key_flag\s*=\s*0\s*;'
    r'\s*_root\.Display_say\[0\]\s*=\s*1\s*;'
    r'\s*_root\.CopyMovie\(\s*"mt_say_01"\s*,\s*"mtsay_001"\s*,\s*1350\s*,\s*380\s*,\s*207\s*\)\s*;'
    r'\s*_root\.mtsay_001\.gotoAndPlay\(\s*"say_three"\s*\)\s*;'
    r'\s*_root\.mt_GetMoney\[0\]\s*=\s*1\s*;'
    r'\s*_root\.mt_changes\s*=\s*0\s*;'
    r'\s*_root\.mt_LastGame_ID\s*=\s*1\s*;\s*\}'
)


def _one(source: str, pattern: str, label: str) -> re.Match:
    matches = list(re.finditer(pattern, source, re.MULTILINE | re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {label} source anchor, found {len(matches)}")
    return matches[0]


def _function(source: str, name: str) -> tuple[str, int]:
    """Get a top-level FFDec function by its unindented closing brace.

    Reject ambiguous/missing boundaries rather than accepting an assignment
    elsewhere in the file as proof of a path.
    """
    start = _one(source, rf"^function[ \t]+{name}\([ \t]*\)[ \t]*\r?\n\{{", f"{name} declaration")
    tail = source[start.end():]
    end = re.search(r"(?m)^}[ \t\r]*$", tail)
    if end is None:
        raise ValueError(f"missing top-level {name} closing brace")
    return tail[:end.start()], start.end()


def audit_paths_from_verified_sources(load: Callable[[str], tuple[str, str]]) -> dict:
    """Check exact source anchors; caller must verify source provenance."""
    initial, initial_sha = load(INIT)
    control, control_sha = load(CONTROL)
    init = _one(initial, r"^[ \t]*mt_LastGame_ID[ \t]*=[ \t]*0[ \t]*;[ \t\r]*$",
                "initial mt_LastGame_ID=0")
    event = _one(control, EVENT, "tile-24 guarded mt_LastGame_ID=1")
    save_body, save_offset = _function(control, "SaveData")
    load_body, load_offset = _function(control, "LoadData")
    checks = {
        "save_terminal_guard": (save_body, save_offset,
            r"_root\.save_mt_LastGame_ID\s*=\s*Number\(\s*_root\.mt_LastGame_ID\s*\)\s*;"),
        "load_terminal_guard": (load_body, load_offset,
            r"_root\.mt_LastGame_ID\s*=\s*Number\(\s*_root\.save_mt_LastGame_ID\s*\)\s*;"),
        "save_dialogue_array": (save_body, save_offset,
            r"_root\.save_Display_say\[temp_i\]\s*=\s*Number\(\s*_root\.Display_say\[temp_i\]\s*\)\s*;"),
        "load_dialogue_array": (load_body, load_offset,
            r"_root\.Display_say\[temp_i\]\s*=\s*Number\(\s*_root\.save_Display_say\[temp_i\]\s*\)\s*;"),
    }
    save_load = {}
    for label, (body, offset, pattern) in checks.items():
        match = _one(body, pattern, label)
        save_load[label] = {"line": control.count("\n", 0, offset + match.start()) + 1}
    for name, body in [("SaveData", save_body), ("LoadData", load_body)]:
        _one(body, r"while\s*\(\s*temp_i\s*<\s*_root\.save_Display_say\.length\s*\)",
             f"{name} dialogue array loop bound")
    return {
        "schema_version": 1,
        "sources": {INIT: initial_sha, CONTROL: control_sha},
        "initial": {"path": INIT, "line": initial.count("\n", 0, init.start()) + 1, "value": 0},
        "tile_event": {"path": CONTROL, "line": control.count("\n", 0, event.start()) + 1,
                       "tile_id": 24, "mt_changes": 1, "my_love": 0,
                       "assigned_mt_LastGame_ID": 1,
                       "same_guarded_block_verified": True},
        "save_load": {"path": CONTROL, **save_load,
                      "dialogue_array_loop_bounds_verified_as_text": True},
        "source_anchors_verified": True,
        "runtime_branch_reachability_verified": False,
        "save_data_roundtrip_executed": False,
        "flash_ending_verified": False,
        "dual_client_parity_verified": False,
        "gymnasium_ready": False,
        "kaggle_started": False,
    }


def audit_paths(manifest: dict, export_root: Path, swf_bytes: bytes) -> dict:
    provenance = audit_candidates(manifest, export_root, swf_bytes)
    entries = {item["path"]: item for item in manifest["files"]}
    root = export_root.resolve()

    def load(path: str) -> tuple[str, str]:
        if path not in entries:
            raise ValueError(f"missing original source: {path}")
        file = export_root / path
        if file.is_symlink() or not file.resolve().is_relative_to(root):
            raise ValueError(f"unsafe original source: {path}")
        raw = file.read_bytes()
        digest = sha256(raw)
        if len(raw) != entries[path]["size"] or digest != entries[path]["sha256"]:
            raise ValueError(f"source changed after provenance check: {path}")
        return raw.decode("utf-8-sig"), digest

    report = audit_paths_from_verified_sources(load)
    report.update({"swf_sha256": provenance["swf_sha256"],
                   "source_manifest_verified": provenance["source_manifest_verified"],
                   "script_files_checked": provenance["script_files_checked"]})
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--swf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit_paths(json.loads(args.manifest.read_text(encoding="utf-8")),
                             args.export_root, args.swf.read_bytes())
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, UnicodeDecodeError, KeyError) as exc:
        parser.exit(2, f"FAIL: original terminal guard paths: {exc}\n")
    print("PASS: source-hashed initial, tile-24 guard, SaveData/LoadData textual anchors; "
          "runtime, ending, dual-client parity and RL NOT VERIFIED")


if __name__ == "__main__":
    main()
