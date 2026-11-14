"""Audit two independent FFDec shop script exports; not gameplay parity."""
import argparse
import hashlib
import json
from pathlib import Path

SWF_SHA256 = "04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9"
FRAMES = (2, 4)
RELATIVE = "scripts/DefineSprite_671_mt_buy/frame_{frame}/DoAction.as"


def audit(first: Path, second: Path, swf: Path) -> dict:
    if not swf.is_file():
        raise ValueError("original SWF missing")
    swf_sha = hashlib.sha256(swf.read_bytes()).hexdigest()
    if swf_sha != SWF_SHA256:
        raise ValueError("original game.swf SHA256 mismatch")
    sources = []
    for frame in FRAMES:
        relative = RELATIVE.format(frame=frame)
        a, b = first / relative, second / relative
        if not a.is_file() or not b.is_file():
            raise ValueError(f"shop frame {frame} missing independent export")
        left, right = a.read_bytes(), b.read_bytes()
        if not left.strip() or not right.strip():
            raise ValueError(f"shop frame {frame} empty or whitespace-only export")
        if left != right:
            raise ValueError(f"shop frame {frame} FFDec exports differ")
        sources.append({"frame": frame, "path": relative, "size": len(left),
                        "sha256": hashlib.sha256(left).hexdigest()})
    return {"schema_version": 1, "swf_sha256": swf_sha, "shop_sources": sources,
            "independent_exports_identical": True, "actionrecord_verified": False,
            "shop_behavior_verified": False, "pygame_html5_parity_verified": False,
            "gymnasium_ready": False, "kaggle_started": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--swf", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.first, args.second, args.swf)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (ValueError, OSError) as exc:
        parser.exit(2, f"FAIL: shop source audit: {exc}\n")
    print("PASS: shop FFDec exports identical; ActionRecord and gameplay parity NOT VERIFIED")


if __name__ == "__main__":
    main()
