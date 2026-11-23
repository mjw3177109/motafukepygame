"""Fail-closed prerequisite gate before launching Kaggle RL."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def verify(evidence: dict) -> None:
    if not evidence.get("all_floors_verified"):
        raise ValueError("all original floors must pass replay verification")
    if not evidence.get("all_events_verified"):
        raise ValueError("all original events and formulas must be verified")
    if not evidence.get("pygame_approved") or not evidence.get("html5_approved"):
        raise ValueError("both clients require visual and functional signoff")
    if not evidence.get("ending_verified"):
        raise ValueError("original ending / clear conditions not verified")
    if not evidence.get("original_swf_sha256") or len(evidence["original_swf_sha256"]) != 64:
        raise ValueError("original SWF SHA256 required")
    if not evidence.get("replay_evidence"):
        raise ValueError("replay evidence references required")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=Path("evidence/parity_signoff.json"))
    args = parser.parse_args()
    if not args.evidence.is_file():
        sys.exit("TRAINING BLOCKED: parity signoff file missing. Do not train on invented rules.")
    try:
        verify(json.loads(args.evidence.read_text(encoding="utf-8")))
    except (ValueError, json.JSONDecodeError) as exc:
        sys.exit("TRAINING BLOCKED: " + str(exc))
    print("Prerequisite declaration found; independently check supporting files before Kaggle training.")


if __name__ == "__main__":
    main()
