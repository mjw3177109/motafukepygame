"""Audit original floor sprite aliases against explicitly evidenced FFDec exports.

A structurally mapped alias is NOT proof of correct Flash registration or pixel parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.floor_tile_plan import plan_jump_floor_tiles

SHA = re.compile(r"[0-9a-f]{64}\Z")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def _safe_path(value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in (".", "..") for part in value.split("/")) and "//" not in value


def _sha(value):
    return isinstance(value, str) and bool(SHA.fullmatch(value))


def _export_inventory(manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("FFDec manifest must contain a files array")
    inventory = {}
    for item in manifest["files"]:
        if not isinstance(item, dict) or not _safe_path(item.get("path")) or not _sha(item.get("sha256")):
            raise ValueError("invalid FFDec inventory entry")
        if item["path"] in inventory:
            raise ValueError("duplicate FFDec export path")
        inventory[item["path"]] = item["sha256"]
    return inventory


def audit_floor_assets(floors, manifest=None, bindings=None, export_root=None):
    """Produce a missing-work inventory; never assert gameplay or pixel parity."""
    if not isinstance(floors, dict) or not isinstance(floors.get("source"), dict):
        raise ValueError("missing original floor provenance")
    swf_hash = floors["source"].get("swf_sha256")
    if not _sha(swf_hash):
        raise ValueError("invalid original SWF SHA256")
    matrices = floors.get("floors")
    if not isinstance(matrices, dict) or set(matrices) != {f"{n:02d}" for n in range(27)}:
        raise ValueError("expected all original floors 00..26")
    per_floor = {}
    required = set()
    for floor in range(1, 27):
        key = f"{floor:02d}"
        plan = plan_jump_floor_tiles(matrices[key])
        sources = sorted({p["source"] for p in plan["placements"]})
        per_floor[key] = {"placement_count": len(plan["placements"]), "source_count": len(sources)}
        required.update(sources)
    # Floor 00 uses a different entry path, not SetLineDisplay(1).
    inventory = {}
    if manifest is not None:
        if not isinstance(manifest, dict) or not isinstance(manifest.get("original"), dict) or manifest["original"].get("sha256") != swf_hash:
            raise ValueError("FFDec manifest source SWF does not match committed floors")
        inventory = _export_inventory(manifest)
    if bindings is not None:
        if manifest is None or export_root is None:
            raise ValueError("bindings require both FFDec manifest and export root")
        if not isinstance(bindings, dict) or type(bindings.get("schema_version")) is not int or bindings["schema_version"] != 1 or bindings.get("swf_sha256") != swf_hash or not isinstance(bindings.get("bindings"), dict):
            raise ValueError("invalid or mismatched asset binding manifest")
    declared = bindings["bindings"] if bindings is not None else {}
    if set(declared) - required:
        raise ValueError("asset bindings contain source aliases not required by floors 01..26")
    mapped, invalid = [], {}
    for source in sorted(declared):
        entry = declared[source]
        problem = None
        if not isinstance(entry, dict):
            problem = "binding must be an object"
        else:
            image_path, image_sha = entry.get("export_path"), entry.get("sha256")
            evidence_path, evidence_sha = entry.get("registration_evidence_path"), entry.get("registration_evidence_sha256")
            ox, oy = entry.get("origin_x"), entry.get("origin_y")
            if (not _safe_path(image_path) or PurePosixPath(image_path).suffix.lower() not in IMAGE_EXTENSIONS or
                    not _sha(image_sha) or inventory.get(image_path) != image_sha):
                problem = "image missing from hashed FFDec inventory"
            elif (not _safe_path(evidence_path) or not _sha(evidence_sha) or inventory.get(evidence_path) != evidence_sha):
                problem = "registration evidence missing from hashed FFDec inventory"
            elif (type(ox) not in (int, float) or type(oy) not in (int, float) or
                  not math.isfinite(ox) or not math.isfinite(oy)):
                problem = "registration offsets must be finite numbers"
            elif not isinstance(entry.get("review_note"), str) or not entry["review_note"].strip():
                problem = "missing human registration review note"
            else:
                root = Path(export_root).resolve()
                for path, digest in ((image_path, image_sha), (evidence_path, evidence_sha)):
                    target = (root / path).resolve()
                    if not target.is_relative_to(root) or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                        problem = "exported file missing or digest differs from FFDec inventory"
                        break
        if problem:
            invalid[source] = problem
        else:
            mapped.append(source)
    missing = sorted(required - set(mapped))
    return {
        "schema_version": 1,
        "swf_sha256": swf_hash,
        "scope": "SetLineDisplay(1), floors 01..26; floor 00 excluded",
        "required_source_count": len(required),
        "required_sources": sorted(required),
        "mapped_source_count": len(mapped),
        "mapped_sources": mapped,
        "missing_sources": missing,
        "invalid_bindings": invalid,
        "per_floor": per_floor,
        "structurally_complete": not missing and not invalid,
        "visual_parity_verified": False,
        "gameplay_parity_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--floors", type=Path, default=Path("data/original_floors.json"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--bindings", type=Path)
    parser.add_argument("--export-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    read = lambda p: json.loads(p.read_text(encoding="utf-8")) if p else None
    try:
        report = audit_floor_assets(read(args.floors), read(args.manifest), read(args.bindings), args.export_root)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Asset audit invalid: {exc}\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Required aliases: {report['required_source_count']}; structurally mapped: {report['mapped_source_count']}; "
          f"missing: {len(report['missing_sources'])}; visual parity: NOT VERIFIED")
    if args.require_complete and not report["structurally_complete"]:
        parser.exit(2, "Asset mapping incomplete; refusing to claim render readiness\n")


if __name__ == "__main__":
    main()
