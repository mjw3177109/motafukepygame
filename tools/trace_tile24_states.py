"""Source-gated, branch-local tile-24 trace for review; NOT Flash execution.

Only the four audited tile-24 blocks are modeled. Movement, movie clips,
other Move_arrow statements, and a playable game are deliberately excluded.
"""
from __future__ import annotations

from copy import deepcopy
from tools.audit_tile24_branch_order import verify_tile24_branch_order

REQUIRED = {
    "tile_id", "display_say0", "mt_changes", "my_love", "now_line",
    "get_money", "now_key_flag", "last_game_id", "floor20_7_5",
}
BRANCHES = (
    "initial_dialogue", "ending_state_change", "love_dialogue", "floor22_dialogue",
)

# Match the JSON/JavaScript probe integer domain; never silently round state IDs.
MAX_SAFE_INTEGER = (1 << 53) - 1


def trace_tile24_states(state: dict, actionscript: str) -> dict:
    """Hypothetical branch-local trace; NOT Flash runtime or dual-client parity."""
    if not isinstance(actionscript, str):
        raise ValueError("ActionScript source is required")
    proof = verify_tile24_branch_order(actionscript)
    if ([x["branch"] for x in proof["source_order"]] != list(BRANCHES)
            or not proof["independent_if_statements_verified"]
            or not proof["love_dialogue_both_arms_verified"]
            or not proof["floor22_three_item_both_arms_verified"]):
        raise ValueError("tile-24 source audit incomplete")
    if type(state) is not dict or set(state) != REQUIRED:
        raise ValueError("exact tile-24 review state fields required")
    flags = ("display_say0", "mt_changes", "my_love", "now_key_flag", "last_game_id")
    if any(type(state[k]) is not int or state[k] not in (0, 1) for k in flags):
        raise ValueError("binary state flags required")
    if (type(state["tile_id"]) is not int or not 0 <= state["tile_id"] <= MAX_SAFE_INTEGER
            or type(state["now_line"]) is not int or not 0 <= state["now_line"] <= 26
            or type(state["floor20_7_5"]) is not int
            or abs(state["floor20_7_5"]) > MAX_SAFE_INTEGER):
        raise ValueError("invalid tile, floor or map cell")
    items = state["get_money"]
    if (type(items) is not list or len(items) != 3
            or any(type(x) is not int or x not in (0, 1) for x in items)):
        raise ValueError("exactly three binary item flags required")

    next_state = deepcopy(state)
    trace = []
    if next_state["tile_id"] == 24:
        if next_state["display_say0"] == 0:
            next_state["display_say0"] = 1
            trace.append({"branch": "initial_dialogue", "clip_command": "CopyMovie(mt_say_01)"})
        if next_state["mt_changes"] == 1 and next_state["my_love"] == 0:
            next_state["mt_changes"] = 0
            next_state["last_game_id"] = 1
            trace.append({"branch": "ending_state_change", "dialogue_command": "say_three"})
        if next_state["my_love"] == 1:
            dialogue = "say_four" if next_state["get_money"][0] == 1 else "say_two"
            next_state["floor20_7_5"] = 13
            next_state["my_love"] = 0
            next_state["mt_changes"] = 0
            trace.append({"branch": "love_dialogue", "dialogue_command": dialogue})
        if next_state["now_line"] == 22:
            next_state["now_key_flag"] = 0
            next_state["display_say0"] = 1
            dialogue = "say_six" if all(x == 1 for x in next_state["get_money"]) else "say_five"
            trace.append({"branch": "floor22_dialogue", "clip_command": "CopyMovie(mt_say_01)",
                          "dialogue_command": dialogue})
    return {
        "state": next_state,
        "trace": trace,
        "source_branch_order_verified": True,
        "branch_local_hypothesis_only": True,
        "flash_runtime_verified": False,
        "dual_client_parity_verified": False,
        "gymnasium_ready": False,
    }
