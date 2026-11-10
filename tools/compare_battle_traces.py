"""Compare observed battle traces; never infer Flash parity from missing data."""
import argparse
import json
from pathlib import Path
from tools.validate_flash_battle_trace import validate

STATE_FIELDS = ("floor", "x", "y", "hp", "money", "exp", "monster_id",
                "monster_present", "battle_phase", "game_over")


def compare(flash_path, candidate_path):
    errors = []
    for name, path in (("flash", flash_path), ("candidate", candidate_path)):
        errors.extend(f"{name}: {e}" for e in validate(path))
    if errors:
        return errors
    flash = [json.loads(line) for line in Path(flash_path).read_text(encoding="utf-8").splitlines()]
    candidate = [json.loads(line) for line in Path(candidate_path).read_text(encoding="utf-8").splitlines()]
    if any(row["source"] != "flash" for row in flash):
        errors.append("reference must be an original Flash trace")
    if any(row["source"] not in ("pygame", "html5") for row in candidate):
        errors.append("candidate must be Pygame or HTML5")
    if len(flash) != len(candidate):
        errors.append(f"step count mismatch: flash={len(flash)} candidate={len(candidate)}")
    for index, (original, actual) in enumerate(zip(flash, candidate)):
        if original["case_id"] != actual["case_id"] or original["action"] != actual["action"]:
            errors.append(f"step {index}: case/action mismatch")
        if original["verified"] is not True or actual["verified"] is not True:
            errors.append(f"step {index}: unverified observation")
        for field in STATE_FIELDS:
            if original[field] is None or actual[field] is None:
                errors.append(f"step {index}: {field} not observed on both sides")
            elif original[field] != actual[field]:
                errors.append(f"step {index}: {field} differs: flash={original[field]!r} candidate={actual[field]!r}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("flash", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    errors = compare(args.flash, args.candidate)
    for error in errors:
        print("FAIL:", error)
    if errors:
        raise SystemExit(1)
    print("PASS: supplied observed steps agree; full game parity NOT VERIFIED")


if __name__ == "__main__":
    main()
