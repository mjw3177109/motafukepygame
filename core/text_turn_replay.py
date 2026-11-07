"""Explicit event replay for evidenced arrow turns and text sprite phases.

A caller must supply frame32/cleanup actions when those Flash frames really run.
This probe never advances a sprite clock or simulates the actual ending screen.
"""
from copy import deepcopy
from core.text_lifecycle_probe import step_text_lifecycle


def replay_text_turns(world: dict, actions: list, monsters: dict, arrow_step=None) -> dict:
    if not isinstance(world, dict) or not isinstance(actions, list):
        raise ValueError("world must be an object and actions must be a list")
    if arrow_step is None:
        from core.arrow_turn_probe import step_arrow_turn
        arrow_step = step_arrow_turn
    state = deepcopy(world)
    trace = []
    game_over_requested = False
    for index, action in enumerate(actions):
        if game_over_requested:
            raise ValueError("game_over requested; subsequent inputs require an implemented ending")
        if not isinstance(action, dict) or not isinstance(action.get("type"), str):
            raise ValueError("each action must have a type")
        kind = action["type"]
        if kind == "arrow":
            if set(action) - {"type", "arrow_id", "critical_rolls"}:
                raise ValueError("unsupported arrow action fields")
            result = arrow_step(state, action.get("arrow_id"), monsters,
                                action.get("critical_rolls", []))
            effects = []
        elif kind in ("text_frame32", "text_cleanup"):
            if set(action) != {"type"}:
                raise ValueError("text sprite actions do not take arrow inputs or rolls")
            result = step_text_lifecycle(state, "frame32" if kind == "text_frame32" else "cleanup")
            effects = result["effects"]
        else:
            raise ValueError("unsupported action type: " + kind)
        state = result["state"]
        game_over_requested = "goto_game_over" in effects
        trace.append({"step": index, "type": kind, "event": result["event"],
                      "effects": effects, "state": deepcopy(state)})
    return {"state": state, "trace": trace, "game_over_requested": game_over_requested}
