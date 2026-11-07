"""Strict JSONL replay comparison. Never approves a port with missing evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_trace(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError("empty replay trace: " + str(path))
    trace = []
    for index, line in enumerate(lines, 1):
        value = json.loads(line)
        if not isinstance(value, dict) or "action" not in value or "state" not in value:
            raise ValueError(f"{path}:{index} requires action and state")
        trace.append(value)
    return trace


def compare(golden: list[dict], candidate: list[dict]) -> list[dict]:
    differences = []
    if len(golden) != len(candidate):
        differences.append({"kind": "length", "original": len(golden), "candidate": len(candidate)})
    for i, (expected, actual) in enumerate(zip(golden, candidate)):
        if expected != actual:
            differences.append({"kind": "step", "step": i,
                                "original": expected, "candidate": actual})
    return differences


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    golden = load_trace(args.golden)
    candidate = load_trace(args.candidate)
    diffs = compare(golden, candidate)
    report = {"status": "pass" if not diffs else "fail",
              "steps_original": len(golden), "steps_candidate": len(candidate),
              "difference_count": len(diffs), "differences": diffs[:20],
              "scope": "supplied replay traces only; NOT a whole-game certification"}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if diffs:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
