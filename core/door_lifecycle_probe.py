"""Narrow FFDec-evidenced door sprite completion / sprite855 cleanup; no frame clock."""
from copy import deepcopy

DOOR_SPRITE_FRAMES = {"mt_15": 5, "mt_05": 10, "mt_03": 10, "mt_04": 10, "mt_02": 10}


def step_door_lifecycle(snapshot: dict, phase: str, *, sprite: str | None = None,
                        frame: int | None = None) -> dict:
    if not isinstance(snapshot, dict) or phase not in ("frame_complete", "cleanup"):
        raise ValueError("expected snapshot and phase frame_complete/cleanup")
    if type(snapshot.get("open_room")) is not int or type(snapshot.get("key_flag")) is not int:
        raise ValueError("open_room and key_flag integers required")
    state = deepcopy(snapshot)
    if phase == "frame_complete":
        if not isinstance(sprite, str) or sprite not in DOOR_SPRITE_FRAMES or type(frame) is not int or DOOR_SPRITE_FRAMES[sprite] != frame:
            raise ValueError("unverified door sprite/frame")
        if state["open_room"] != 1:
            raise ValueError("door frame requires open_room=1")
        state["open_room"] = 2
        return {"state": state, "event": "door_ready_for_cleanup", "effects": []}
    if sprite is not None or frame is not None:
        raise ValueError("cleanup does not accept sprite/frame")
    if state["open_room"] != 2:
        raise ValueError("door cleanup requires open_room=2")
    x, y = state.get("last_x"), state.get("last_y")
    if type(x) is not int or type(y) is not int or not (0 <= x < 11 and 0 <= y < 11):
        raise ValueError("door cleanup requires original Last_x/Last_y")
    state["open_room"] = 0
    state["key_flag"] = 1
    return {"state": state, "event": "door_removed",
            "effects": ["remove_map_sprite:mt_m_" + str(x) + "_" + str(y)]}
