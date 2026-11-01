"""Source-linked candidate index for Flash death/ending control flow.

This indexes decompiled text, not executable control flow or Flash behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SWF_SHA256 = "04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9"
PATTERNS = {
    "game_over_mention": re.compile(r"\bgame_over\b", re.IGNORECASE),
    "hero_hp_comparison": re.compile(
        r"(?:\b(?:Now_hp|right_hp)\b\s*(?:<=|>=|==|!=|<|>)"
        r"|(?:<=|>=|==|!=|<|>)\s*\b(?:Now_hp|right_hp)\b)"
    ),
    # Textual assignment candidates only; no claim about executed branches.
    # Include indexed array writes and whole-array resets, but exclude == / ===.
    "terminal_state_write": re.compile(
        r"(?<![\w$])(?P<target>(?:_root\.)?"
        r"(?:Display_text|mt_LastGame_ID"
        r"|Display_say(?:[ \t]*\[[^\]\r\n]+\])?"
        r"|mt_line_26(?:[ \t]*\[[^\]\r\n]+\](?:[ \t]*\[[^\]\r\n]+\])?)?))"
        r"[ \t]*(?P<operator>\+\+|--|\+=|-=|\*=|/=|%=|=(?!=))"
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_window(lines: list[str], line: int, before: int = 24, after: int = 8) -> list[dict]:
    """Show decompiled neighboring lines, without inferring a branch or runtime behavior."""
    first = max(1, line - before)
    last = min(len(lines), line + after)
    return [
        {"line": n, "text": lines[n - 1][:400],
         "truncated": len(lines[n - 1]) > 400}
        for n in range(first, last + 1)
    ]


def audit_candidates(manifest: dict, export_root: Path, swf_bytes: bytes) -> dict:
    if sha256(swf_bytes) != SWF_SHA256:
        raise ValueError("original game.swf SHA256 mismatch")
    if manifest.get("original", {}).get("sha256") != SWF_SHA256:
        raise ValueError("FFDec manifest SWF SHA256 mismatch")
    entries = {}
    for item in manifest.get("files", []):
        path = item.get("path", "")
        if not path.startswith("scripts/") or not path.lower().endswith(".as"):
            continue
        if path in entries or ".." in Path(path).parts or Path(path).is_absolute():
            raise ValueError("duplicate or unsafe script path")
        entries[path] = item
    if not entries:
        raise ValueError("FFDec manifest contains no ActionScript files")
    root = export_root.resolve()
    actual = {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file() and p.relative_to(root).as_posix().startswith("scripts/")
        and p.suffix.lower() == ".as"
    }
    if actual != set(entries):
        raise ValueError("ActionScript inventory differs from FFDec manifest")
    hits = []
    for path, item in sorted(entries.items()):
        file = export_root / path
        if file.is_symlink() or not file.resolve().is_relative_to(root):
            raise ValueError("unsafe ActionScript source")
        raw = file.read_bytes()
        if sha256(raw) != item.get("sha256") or len(raw) != item.get("size"):
            raise ValueError("ActionScript bytes differ from FFDec manifest: " + path)
        source = raw.decode("utf-8-sig")
        lines = source.splitlines()
        seen = set()
        for kind, pattern in PATTERNS.items():
            for match in pattern.finditer(source):
                line = source.count("\n", 0, match.start()) + 1
                key = (kind, line)
                if key in seen:
                    continue
                seen.add(key)
                hit = {
                    "kind": kind, "path": path, "line": line,
                    "source_sha256": sha256(raw),
                    "snippet": lines[line - 1].strip()[:240],
                    "source_context": source_window(lines, line),
                }
                if kind == "terminal_state_write":
                    hit["target"] = match.group("target")
                    hit["operator"] = match.group("operator")
                hits.append(hit)
    hits.sort(key=lambda h: (h["kind"], h["path"], h["line"]))
    counts = {name: sum(h["kind"] == name for h in hits)
              for name in PATTERNS if name != "terminal_state_write"}
    write_count = sum(h["kind"] == "terminal_state_write" for h in hits)
    return {
        "schema_version": 2, "swf_sha256": SWF_SHA256,
        "script_files_checked": len(entries), "source_manifest_verified": True,
        "candidate_counts": counts, "state_write_candidate_count": write_count,
        "candidates": hits,
        "candidates_are_text_matches_not_control_flow_proof": True,
        "state_writes_are_text_candidates_not_proven_assignments": True,
        "source_context_is_decompiled_text_not_control_flow_proof": True,
        "game_over_may_be_a_frame_label_not_a_script_mention": True,
        "flash_runtime_verified": False, "death_behavior_verified": False,
        "ending_verified": False, "dual_client_parity_verified": False,
        "gymnasium_ready": False, "kaggle_started": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--swf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit_candidates(
            json.loads(args.manifest.read_text(encoding="utf-8")),
            args.export_root, args.swf.read_bytes()
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, UnicodeDecodeError, KeyError) as exc:
        parser.exit(2, f"FAIL: original terminal candidate inventory: {exc}\n")
    print(f"PASS: {report['script_files_checked']} manifest-hashed ActionScript files; "
          f"candidates={report['candidate_counts']}; "
          f"state_writes={report['state_write_candidate_count']}; death/ending NOT VERIFIED")
    for hit in report["candidates"][:24]:
        print(f"CANDIDATE {hit['kind']} {hit['path']}:{hit['line']} {hit['snippet']}")
        if hit["kind"] == "game_over_mention":
            for row in hit["source_context"]:
                suffix = " [truncated]" if row["truncated"] else ""
                print(f"CONTEXT {hit['path']}:{row['line']} {row['text']}{suffix}")


if __name__ == "__main__":
    main()
