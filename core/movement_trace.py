"""Deterministic, fail-closed traces of the verified Move_arrow subset.

Regression probe only: does not implement Flash input gating or runtime parity.
"""
from copy import deepcopy
from core.movement_probe import step_move_arrow


def trace_move_arrows(initial_state: dict, arrow_ids: list[int]) -> dict:
    """Snapshot each probe step without mutating the supplied state.

    Unsupported tiles and invalid inputs raise, never return partial success.
    """
    if type(arrow_ids) is not list:
        raise ValueError("arrow_ids must be a list")
    state = deepcopy(initial_state)
    frames = []
    for index, arrow_id in enumerate(arrow_ids):
        result = step_move_arrow(state, arrow_id)
        state = result["state"]
        frames.append({"index": index, "arrow_id": arrow_id,
                       "event": result["event"], "state": deepcopy(state)})
    return {"initial_state": deepcopy(initial_state), "frames": frames,
            "final_state": deepcopy(state)}
