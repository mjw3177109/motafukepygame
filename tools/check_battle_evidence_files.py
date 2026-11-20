"""Optional strict evidence-file check; does not assert Flash parity."""
import argparse
import json
from pathlib import Path


def check(trace, evidence_root):
    root = Path(evidence_root).resolve()
    errors = []
    try:
        rows = Path(trace).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [f"cannot read trace: {exc}"]
    if not rows:
        return ["empty trace"]
    for index, line in enumerate(rows, 1):
        try:
            row = json.loads(line)
        except (ValueError, TypeError):
            errors.append(f"line {index}: invalid JSON")
            continue
        if not isinstance(row, dict):
            errors.append(f"line {index}: expected object")
            continue
        if row.get("verified") is not True:
            continue
        frame = row.get("evidence_frame")
        if not isinstance(frame, str) or not frame.strip():
            errors.append(f"line {index}: missing evidence_frame")
            continue
        relative = Path(frame)
        if relative.is_absolute() or "\\" in frame or ":" in frame or ".." in relative.parts:
            errors.append(f"line {index}: unsafe evidence_frame path")
            continue
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            errors.append(f"line {index}: evidence_frame not found within root")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    errors = check(args.trace, args.evidence_root)
    for error in errors:
        print("FAIL:", error)
    if errors:
        raise SystemExit(1)
    print("PASS: referenced files exist; Flash parity NOT VERIFIED")


if __name__ == "__main__":
    main()
