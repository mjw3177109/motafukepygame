"""Validate structural integrity of battle trace JSONL; never claims game parity."""
import argparse
import json
from pathlib import Path

REQUIRED = {"schema_version", "source", "case_id", "step", "action", "floor",
            "x", "y", "hp", "money", "exp", "monster_id", "monster_present",
            "battle_phase", "game_over", "evidence_frame", "verified"}
SOURCES = {"flash", "pygame", "html5"}


def validate(path):
    errors = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [f"cannot read trace: {exc}"]
    if not lines:
        return ["empty trace"]
    expected_source = expected_case = None
    expected_step = 0
    for line_no, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"line {line_no}: invalid JSON")
            continue
        if not isinstance(row, dict):
            errors.append(f"line {line_no}: expected object")
            continue
        missing = REQUIRED - row.keys()
        if missing:
            errors.append(f"line {line_no}: missing {sorted(missing)}")
            continue
        if type(row["schema_version"]) is not int or row["schema_version"] != 1:
            errors.append(f"line {line_no}: unsupported schema")
        if not isinstance(row["source"], str) or row["source"] not in SOURCES:
            errors.append(f"line {line_no}: invalid source")
        if not isinstance(row["case_id"], str) or not row["case_id"]:
            errors.append(f"line {line_no}: invalid case_id")
        if type(row["step"]) is not int or row["step"] != expected_step:
            errors.append(f"line {line_no}: expected step {expected_step}")
        if not isinstance(row["action"], str) or not row["action"]:
            errors.append(f"line {line_no}: invalid action")
        if type(row["verified"]) is not bool:
            errors.append(f"line {line_no}: verified must be boolean")
        if row["verified"] is True and not row["evidence_frame"]:
            errors.append(f"line {line_no}: verified requires evidence_frame")
        for key in ("floor", "x", "y", "hp", "money", "exp"):
            if row[key] is not None and type(row[key]) is not int:
                errors.append(f"line {line_no}: {key} must be integer or null")
        for key in ("monster_present", "game_over"):
            if row[key] is not None and type(row[key]) is not bool:
                errors.append(f"line {line_no}: {key} must be boolean or null")
        if expected_source is not None and row["source"] != expected_source:
            errors.append(f"line {line_no}: mixed sources")
        if expected_case is not None and row["case_id"] != expected_case:
            errors.append(f"line {line_no}: mixed cases")
        expected_source, expected_case = row["source"], row["case_id"]
        expected_step += 1
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    errors = validate(args.trace)
    for error in errors:
        print("FAIL:", error)
    if errors:
        raise SystemExit(1)
    print("PASS: trace structure only; original Flash parity NOT VERIFIED")


if __name__ == "__main__":
    main()
