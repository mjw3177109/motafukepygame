"""Prioritize original floor sprites for manual review using source-hashed SWF reports.

A source review queue is not an approved image binding, visual parity, or gameplay parity.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{64}\Z")
ALIAS = re.compile(r"mt_\d+\Z")
IDENTITY = {"a_fixed16": 65536, "b_fixed16": 0, "c_fixed16": 0,
            "d_fixed16": 65536, "tx_twips": 0, "ty_twips": 0}


def build_queue(coverage: dict, trace: dict, frames: dict, placements: dict) -> dict:
    reports = (coverage, trace, frames, placements)
    if any(not isinstance(r, dict) or r.get("schema_version") != 1 for r in reports):
        raise ValueError("invalid report schema")
    swf = coverage.get("swf_sha256")
    if not isinstance(swf, str) or not SHA.fullmatch(swf) or any(r.get("swf_sha256") != swf for r in reports):
        raise ValueError("SWF source provenance mismatch")
    tag_sha = trace.get("ffdec_tag_dump_sha256")
    if not isinstance(tag_sha, str) or not SHA.fullmatch(tag_sha) or any(
        r.get("ffdec_tag_dump_sha256") != tag_sha for r in (frames, placements)
    ):
        raise ValueError("FFDec tag dump provenance mismatch")
    required = coverage.get("required_sources")
    symbols, sprites, snapshots = trace.get("symbols"), frames.get("sprites"), placements.get("sprites")
    if (not isinstance(required, list) or not required or
        any(not isinstance(a, str) or not ALIAS.fullmatch(a) for a in required) or
        len(required) != len(set(required)) or not all(isinstance(x, dict) for x in (symbols, sprites, snapshots)) or
        set(required) != set(symbols) or set(required) != set(sprites) or
        coverage.get("required_source_count") != len(required) or
        trace.get("resolved_symbol_count") != len(required) or
        frames.get("verified_symbol_count") != len(required) or
        frames.get("frame_count_verified") is not True or
        set(snapshots) != set(placements.get("verified_aliases", [])) or
        not set(snapshots).issubset(set(required))):
        raise ValueError("inconsistent alias or frame evidence coverage")
    mapped = coverage.get("mapped_sources")
    missing = coverage.get("missing_sources")
    if (not isinstance(mapped, list) or not isinstance(missing, list) or
        set(mapped) & set(missing) or set(mapped) | set(missing) != set(required) or
        coverage.get("mapped_source_count") != len(mapped) or
        len(mapped) != len(set(mapped)) or len(missing) != len(set(missing))):
        raise ValueError("inconsistent binding coverage")
    items = []
    for alias in required:
        symbol, frame = symbols[alias], sprites[alias]
        if not isinstance(symbol, dict) or not isinstance(frame, dict):
            raise ValueError(f"invalid symbol/frame for {alias}")
        character_id = symbol.get("character_id")
        count = frame.get("frame_count")
        if (type(character_id) is not int or character_id < 1 or
            type(count) is not int or count < 1 or
            frame.get("character_id") != character_id or
            frame.get("define_offset") != symbol.get("define_offset") or
            frame.get("showframe_count") != count):
            raise ValueError(f"source timeline mismatch for {alias}")
        shapes = symbol.get("shape_exports")
        if (not isinstance(shapes, list) or not shapes or
            any(not isinstance(s, dict) or type(s.get("character_id")) is not int or
                not isinstance(s.get("path"), str) or not isinstance(s.get("sha256"), str) or
                not SHA.fullmatch(s["sha256"]) for s in shapes)):
            raise ValueError(f"invalid hashed shapes for {alias}")
        snapshot = snapshots.get(alias)
        if snapshot is not None:
            if (not isinstance(snapshot, dict) or snapshot.get("character_id") != character_id or
                snapshot.get("frame_count") != count or
                not isinstance(snapshot.get("frames"), list) or len(snapshot["frames"]) != count):
                raise ValueError(f"placement snapshot mismatch for {alias}")
        # One frame, one hashed shape, and a decoded identity placement are
        # required before static screenshot review can be queued.
        first = snapshot["frames"][0] if snapshot and count == 1 else None
        placed = first.get("placements") if isinstance(first, dict) else None
        identity = bool(
            count == 1 and len(shapes) == 1 and isinstance(placed, list) and len(placed) == 1 and
            isinstance(placed[0], dict) and placed[0].get("character_id") == shapes[0]["character_id"] and
            placed[0].get("matrix") == IDENTITY and placed[0].get("clip_depth") is None and
            snapshot.get("uninterpreted_action_count") == 0 and
            not first.get("uninterpreted_action_offsets")
        )
        stage = ("static_screenshot_review" if identity else
                 "decode_static_placements" if count == 1 else "decode_animated_timeline")
        items.append({"alias": alias, "character_id": character_id, "frame_count": count,
                      "shape_exports": shapes, "placement_snapshot_verified": snapshot is not None,
                      "review_stage": stage, "binding_structurally_mapped": alias in mapped,
                      "flash_visual_parity_verified": False})
    order = {"static_screenshot_review": 0, "decode_static_placements": 1, "decode_animated_timeline": 2}
    items.sort(key=lambda item: (order[item["review_stage"]], item["frame_count"],
                                 len(item["shape_exports"]), item["alias"]))
    stages = {stage: sum(item["review_stage"] == stage for item in items) for stage in order}
    return {"schema_version": 1, "swf_sha256": swf, "ffdec_tag_dump_sha256": tag_sha,
            "source_alias_count": len(items), "review_stage_counts": stages,
            "queue": items, "binding_approval_inferred": False,
            "visual_parity_verified": False, "gameplay_parity_verified": False,
            "gymnasium_ready": False, "kaggle_started": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("coverage", "trace", "frames", "placements", "out"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    try:
        load = lambda path: json.loads(path.read_text(encoding="utf-8"))
        report = build_queue(load(args.coverage), load(args.trace),
                             load(args.frames), load(args.placements))
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Original asset review queue FAILED: {exc}\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PASS: {report['source_alias_count']} source-linked aliases queued; "
          f"stages={report['review_stage_counts']}; visual/gameplay parity NOT VERIFIED")


if __name__ == "__main__":
    main()
