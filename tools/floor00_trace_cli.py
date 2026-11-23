"""Source-pinned floor-00 movement CLI; diagnostic only, not a playable game.

stdin: {"keys":{"yellow":0,"blue":0,"red":0},"arrow_ids":[1,2]}
stdout: deterministic JSON trace. Unsupported original events fail closed.
"""
import json
from pathlib import Path
import sys

from core.floor00_movement_trace import trace_committed_floor_00
from tools.movement_trace_cli import _reject_duplicate_keys


FLOOR_SOURCE = Path(__file__).resolve().parents[1] / "data" / "original_floors.json"


def run(request: dict) -> str:
    if type(request) is not dict or set(request) != {"keys", "arrow_ids"}:
        raise ValueError("expected keys and arrow_ids only")
    if type(request["arrow_ids"]) is not list:
        raise ValueError("arrow_ids must be a list")
    original = FLOOR_SOURCE.read_text(encoding="utf-8")
    result = trace_committed_floor_00(original, request["keys"], request["arrow_ids"])
    return json.dumps(result, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":"))


def main() -> int:
    try:
        request = json.load(sys.stdin, object_pairs_hook=_reject_duplicate_keys,
                            parse_constant=lambda value: (_ for _ in ()).throw(
                                ValueError("non-finite JSON constant: " + value)))
        output = run(request)
    except (ValueError, TypeError, KeyError, IndexError, OSError) as exc:
        print("floor-00 trace rejected: " + str(exc), file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
