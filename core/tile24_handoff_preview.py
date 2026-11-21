"""Read-only bridge from the arrow router to a source-audited tile-24 review trace.

This is NOT an event executor, a Pygame handler, or evidence of Flash parity.
The caller supplies review_state explicitly; world -> ActionScript state mapping
is deliberately not inferred until a real Flash capture establishes it.
"""
from core.arrow_turn_probe import step_arrow_turn, Tile24HandoffRequired
from tools.trace_tile24_states import trace_tile24_states


def preview_tile24_handoff(world: dict, arrow_id: int, monsters: dict,
                           review_state: dict, actionscript: str) -> dict:
    """Validate movement handoff, then plan commands without applying them."""
    try:
        step_arrow_turn(world, arrow_id, monsters, [])
    except Tile24HandoffRequired as handoff:
        target = list(handoff.target)
    else:
        raise ValueError("no tile-24 handoff for this input")
    if type(review_state) is not dict or type(review_state.get("tile_id")) is not int or review_state["tile_id"] != 24:
        raise ValueError("explicit tile-24 review state required")
    review = trace_tile24_states(review_state, actionscript)
    return {
        "event": "tile24_review_only",
        "target": target,
        "review": review,
        "state_mapping_verified": False,
        "flash_runtime_verified": False,
        "executable": False,
        "gymnasium_ready": False,
    }
