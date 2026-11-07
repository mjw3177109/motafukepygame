"""Deterministic replay of *evidenced* floor-jump menu operations.

This composes existing original-script probes. It deliberately stops at the
SetLineDisplay(1) request: floor redraw and input restoration are not proven.
"""
from copy import deepcopy

from core.jump_lifecycle_probe import step_jump_lifecycle
from core.jump_selection_probe import step_jump_selection


_ALLOWED = {"up", "down", "confirm", "cancel", "cleanup"}


def replay_jump_turns(world: dict, cursor: dict, actions: list) -> dict:
    if not isinstance(world, dict) or not isinstance(cursor, dict) or not isinstance(actions, list):
        raise ValueError("world, cursor and actions must be object, object, list")
    state, selection = deepcopy(world), deepcopy(cursor)
    trace = []
    floor_refresh_pending = False
    for index, action in enumerate(actions):
        if not isinstance(action, dict) or set(action) != {"type"} or type(action["type"]) is not str:
            raise ValueError("jump action must contain only a string type")
        kind = action["type"]
        if kind not in _ALLOWED:
            raise ValueError("unsupported jump action: " + kind)
        if floor_refresh_pending:
            raise ValueError("SetLineDisplay(1) requested; floor redraw not implemented")
        if kind in ("up", "down"):
            result = step_jump_selection(state, selection, 3 if kind == "up" else 4)
            state, selection = result["state"], result["cursor"]
        else:
            result = step_jump_lifecycle(state, selection if kind == "confirm" else None, kind)
            state = result["state"]
        floor_refresh_pending = "set_line_display:1" in result["effects"]
        trace.append({"step": index, "type": kind, "event": result["event"],
                      "effects": deepcopy(result["effects"]),
                      "state": deepcopy(state), "cursor": deepcopy(selection),
                      "floor_refresh_pending": floor_refresh_pending})
    return {"state": state, "cursor": selection, "trace": trace,
            "floor_refresh_pending": floor_refresh_pending}
