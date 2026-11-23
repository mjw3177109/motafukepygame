"""Source-pinned floor-00 movement trace adapter; NOT a playable Flash runtime.

Only verified Move_arrow subset. Unsupported events fail closed. Input gating,
animation, combat, stairs, and ending are not implemented.
"""
from core.initial_floor_loader import plan_committed_floor_00_spawn
from core.original_floor_json import load_original_floor_json
from core.movement_trace import trace_move_arrows


def trace_committed_floor_00(json_text: str, keys: dict, arrow_ids: list[int]) -> dict:
    """Connect source-pinned floor, original spawn, and deterministic probe."""
    spawn = plan_committed_floor_00_spawn(json_text)
    payload = load_original_floor_json(json_text)
    matrix = payload["floors"]["00"]
    if type(keys) is not dict or set(keys) != {"yellow", "blue", "red"}:
        raise ValueError("expected exactly yellow, blue, red key counts")
    hero = spawn["hero"]
    state = {"grid": matrix, "row": hero["row"], "col": hero["col"],
             "keys": keys}
    # Empty sequences must validate state too, not bypass the movement probe.
    from core.movement_probe import step_move_arrow
    if not arrow_ids:
        if type(arrow_ids) is not list:
            raise ValueError("arrow_ids must be a list")
        # A zero-step trace is valid only with a source-pinned floor and inventory.
        if any(type(v) is not int or abs(v) > (1 << 53) - 1 for v in keys.values()):
            raise ValueError("expected safe-integer key inventory")
    return trace_move_arrows(state, arrow_ids)
