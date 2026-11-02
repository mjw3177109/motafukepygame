"""Audit original say-08 frame writes and their textual consumer anchors.

Only FFDec source-text evidence is checked; no execution path is inferred.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from tools.audit_terminal_candidates import audit_candidates, sha256

WRITERS = {6: 2, 9: 5, 12: 9}
CONSUMER = "scripts/DefineSprite_855/frame_1/DoAction.as"


def _require_once(source: str, pattern: str, description: str) -> re.Match:
    hits = list(re.finditer(pattern, source, flags=re.MULTILINE | re.DOTALL))
    if len(hits) != 1:
        raise ValueError(f"expected one {description} source anchor; got {len(hits)}")
    return hits[0]


def _terminal_guard_writes(provenance: dict) -> list[dict]:
    """Preserve hashed text candidates for the ending guard; never infer execution."""
    fields = ("path", "line", "column", "target", "operator",
              "source_sha256", "snippet", "source_context")
    return [
        {field: hit[field] for field in fields}
        for hit in provenance["candidates"]
        if hit["kind"] == "terminal_state_write"
        and hit["target"].removeprefix("_root.") == "mt_LastGame_ID"
    ]


def audit_handoff(manifest: dict, export_root: Path, swf_bytes: bytes) -> dict:
    provenance = audit_candidates(manifest, export_root, swf_bytes)
    guard_writes = _terminal_guard_writes(provenance)
    entries = {item["path"]: item for item in manifest["files"]}

    def load(path: str) -> tuple[str, str]:
        if path not in entries:
            raise ValueError(f"missing original source: {path}")
        raw = (export_root / path).read_bytes()
        if sha256(raw) != entries[path]["sha256"] or len(raw) != entries[path]["size"]:
            raise ValueError(f"source changed after provenance check: {path}")
        return raw.decode("utf-8-sig"), sha256(raw)

    writers = []
    for frame, value in WRITERS.items():
        path = f"scripts/DefineSprite_795_mt_say_08/frame_{frame}/DoAction.as"
        source, digest = load(path)
        match = _require_once(
            source,
            rf"^[ \t]*_root\.Display_say\[8\][ \t]*=[ \t]*{value}[ \t]*;[ \t\r]*$",
            f"say-08 frame {frame} write",
        )
        writers.append({"frame": frame, "value": value, "path": path,
                        "line": source.count("\n", 0, match.start()) + 1,
                        "source_sha256": digest})

    source, digest = load(CONSUMER)
    consumers = []
    for expected, next_value in [(2, 3), (5, 6), (9, 10)]:
        pattern = (
            rf"if\s*\(\s*_root\.Display_say\[8\]\s*==\s*{expected}\s*\)"
            rf"\s*\{{\s*_root\.DelMovie\(\s*\"mtsay_008\"\s*\)\s*;"
            rf"\s*_root\.Display_say\[8\]\s*=\s*{next_value}\s*;"
            rf"\s*_root\.Now_key_flag\s*=\s*1\s*;"
        )
        match = _require_once(source, pattern, f"say-08 consumer {expected}->{next_value}")
        consumers.append({"input": expected, "output": next_value,
                          "line": source.count("\n", 0, match.start()) + 1})

    terminal = _require_once(
        source,
        r"if\s*\(\s*_root\.Display_say\[8\]\s*==\s*9\s*\)\s*\{"
        r"\s*_root\.DelMovie\(\s*\"mtsay_008\"\s*\)\s*;"
        r"\s*_root\.Display_say\[8\]\s*=\s*10\s*;"
        r"\s*_root\.Now_key_flag\s*=\s*1\s*;"
        r"\s*if\s*\(\s*_root\.mt_LastGame_ID\s*==\s*0\s*\)\s*\{"
        r"\s*_root\.DelBaseDisplay\(\)\s*;"
        r"\s*_root\.DelLineDisplay\(\)\s*;"
        r"\s*_root\.gotoAndPlay\(\s*\"game_over\"\s*\)\s*;"
        r"\s*\}\s*if\s*\(\s*_root\.mt_LastGame_ID\s*==\s*1\s*\)",
        "say-08 terminal conditional text",
    )
    return {
        "schema_version": 2,
        "terminal_guard": {
            "variable": "mt_LastGame_ID",
            "write_candidate_count": len(guard_writes),
            "write_candidates": guard_writes,
            "source_writes_are_text_candidates_only": True,
            "runtime_value_proven": False,
        },
        "swf_sha256": provenance["swf_sha256"],
        "source_manifest_verified": provenance["source_manifest_verified"],
        "script_files_checked": provenance["script_files_checked"],
        "writers": writers,
        "consumer": {"path": CONSUMER, "source_sha256": digest,
                     "state_transitions": consumers,
                     "terminal_branch_line": source.count("\n", 0, terminal.start()) + 1},
        "textual_source_anchors_verified": True,
        "execution_order_verified": False,
        "flash_runtime_verified": False,
        "ending_verified": False,
        "dual_client_parity_verified": False,
        "gymnasium_ready": False,
        "kaggle_started": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--swf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit_handoff(json.loads(args.manifest.read_text(encoding="utf-8")),
                               args.export_root, args.swf.read_bytes())
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    except (OSError, ValueError, UnicodeDecodeError, KeyError) as exc:
        parser.exit(2, f"FAIL: original say-08 source handoff: {exc}\n")
    print("PASS: original say-08 frames 6/9/12 and Sprite 855 consumer source "
          f"anchors; mt_LastGame_ID write candidates={report['terminal_guard']['write_candidate_count']}; "
          "execution, ending and Flash parity NOT VERIFIED")


if __name__ == "__main__":
    main()
