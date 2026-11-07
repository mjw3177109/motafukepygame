"""JSON-lines-free, single-request CLI for the verified movement subset.

Input: {"initial_state": {...}, "arrow_ids": [1,2,...]} on stdin.
Output: one canonical JSON trace on stdout. This is not a playable runtime.
"""
import json
import sys

from core.movement_trace import trace_move_arrows


def run(request: dict) -> str:
    if type(request) is not dict or set(request) != {"initial_state", "arrow_ids"}:
        raise ValueError("expected initial_state and arrow_ids only")
    result = trace_move_arrows(request["initial_state"], request["arrow_ids"])
    return json.dumps(result, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":"))


def main() -> int:
    try:
        request = json.load(sys.stdin, parse_constant=lambda x: (_ for _ in ()).throw(
            ValueError("non-finite JSON constant: " + x)))
        output = run(request)
    except (ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
        print("movement trace rejected: " + str(exc), file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
