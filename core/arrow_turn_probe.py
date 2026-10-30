"""Evidence-scoped original keyboard gate and arrow-turn composition.

No real UI, modal completion, animation clock or full game is implemented.
"""
from __future__ import annotations
from copy import deepcopy
from core.movement_probe import DELTAS, step_move_arrow
from core.encounter_pipeline_probe import resolve_encounter

class UnsupportedModalInputError(ValueError):
    """Original Flash would navigate a modal instead of moving."""

def classify_arrow_input(world: dict, arrow_id: int) -> str:
    if type(arrow_id) is not int or arrow_id not in DELTAS:
        raise ValueError("arrow_id must be one of Flash 1,2,3,4")
    flags = ("key_flag", "display_list", "display_jump", "display_text", "display_buy")
    if not isinstance(world, dict) or any(type(world.get(k)) is not int for k in flags):
        raise ValueError("original keyboard gate flags required")
    if (world["key_flag"] == 1 and world["display_list"] == 0
            and world["display_jump"] == 0 and world["display_text"] == 0):
        return "move_arrow"
    if arrow_id in (3, 4) and world["display_buy"] == 1:
        return "buy_modal_unimplemented"
    if arrow_id in (3, 4) and world["display_jump"] == 1:
        return "jump_modal_unimplemented"
    return "input_blocked"

def step_arrow_turn(world: dict, arrow_id: int, monsters: dict,
                    critical_rolls: list | None = None) -> dict:
    if critical_rolls is None:
        critical_rolls = []
    if not isinstance(critical_rolls, list):
        raise ValueError("critical_rolls must be an explicit list")
    gate = classify_arrow_input(world, arrow_id)
    if gate.endswith("_unimplemented"):
        raise UnsupportedModalInputError(gate)
    if gate == "input_blocked":
        if critical_rolls:
            raise ValueError("blocked input cannot consume critical rolls")
        return {"state": deepcopy(world), "event": gate,
                "events": [{"stage": "keyboard", "event": gate}],
                "rolls_used": 0, "cleared": []}
    if world.get("display_kill") != 0:
        raise ValueError("arrow router requires idle display_kill=0")
    row, col = world.get("row"), world.get("col")
    if type(row) is not int or type(col) is not int or not (0 <= row < 11 and 0 <= col < 11):
        raise ValueError("invalid original row/column")
    grid = world.get("grid")
    if not isinstance(grid, list) or len(grid) != 11 or any(
            not isinstance(line, list) or len(line) != 11 or any(type(v) is not int for v in line)
            for line in grid):
        raise ValueError("expected original 11x11 integer grid")
    dr, dc = DELTAS[arrow_id]
    nr, nc = row + dr, col + dc
    tile = grid[nr][nc] if 0 <= nr < 11 and 0 <= nc < 11 else None
    if tile is not None and (40 <= tile <= 70 or tile in (188, 198)):
        result = resolve_encounter(world, arrow_id, monsters, critical_rolls)
        used = next((e["rolls_used"] for e in result["events"] if e["stage"] == "battle"), 0)
        return {"state": result["state"], "event": result["events"][-1]["event"],
                "events": result["events"], "rolls_used": used, "cleared": result["cleared"]}
    if critical_rolls:
        raise ValueError("non-monster movement cannot consume critical rolls")
    result = step_move_arrow(world, arrow_id)
    state, event = result["state"], result["event"]
    if event.startswith("pickup_"):
        state["key_flag"] = 0
        state["display_text"] = 1
    elif event.startswith("open_"):
        state["key_flag"] = 0
        state["open_room"] = 1
        state["last_x"], state["last_y"] = nr, nc
    return {"state": state, "event": event,
            "events": [{"stage": "move_arrow", "event": event}],
            "rolls_used": 0, "cleared": []}

def replay_arrow_turns(world: dict, actions: list, monsters: dict) -> dict:
    """Keep deterministic state snapshots; do not auto-dismiss UI."""
    if not isinstance(actions, list):
        raise ValueError("actions must be a list")
    state = deepcopy(world)
    trace = []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise ValueError("each action must be an object")
        result = step_arrow_turn(state, action.get("arrow_id"), monsters,
                                 action.get("critical_rolls", []))
        state = result["state"]
        trace.append({"step": index, "arrow_id": action["arrow_id"],
                      "event": result["event"], "rolls_used": result["rolls_used"],
                      "state": deepcopy(state)})
    return {"state": state, "trace": trace}
