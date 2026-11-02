"""FFDec-evidenced text frame32 / sprite855 frame1 *sub-branch* only."""
from copy import deepcopy


def step_text_lifecycle(snapshot: dict, phase: str) -> dict:
    if not isinstance(snapshot, dict) or phase not in ("frame32", "cleanup"):
        raise ValueError("expected snapshot and phase frame32/cleanup")
    if type(snapshot.get("display_text")) is not int or type(snapshot.get("key_flag")) is not int:
        raise ValueError("display_text and key_flag integers required")
    state = deepcopy(snapshot)
    if phase == "frame32":
        if state["display_text"] != 1 or type(state.get("boss_kills")) is not int:
            raise ValueError("frame32 requires display_text=1 and boss_kills")
        state["key_flag"] = 0 if state["boss_kills"] == 1 else 1
        state["display_text"] = 2
        return {"state": state, "event": "text_ready_for_cleanup", "effects": []}
    if state["display_text"] != 2 or type(state.get("floor26_cell_3_5")) is not int:
        raise ValueError("cleanup requires display_text=2 and original floor26 cell")
    state["display_text"] = 0
    effects = ["remove_text_sprite"]
    if state["floor26_cell_3_5"] == 0:
        effects.extend(["clear_base_display", "clear_line_display", "goto_game_over"])
    return {"state": state, "event": "game_over_requested" if len(effects) > 1 else "text_removed", "effects": effects}
