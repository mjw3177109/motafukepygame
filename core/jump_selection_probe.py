"""FFDec-evidenced floor-jump menu cursor navigation only (not a floor change)."""
from copy import deepcopy
from math import isfinite


def step_jump_selection(world: dict, cursor: dict, arrow_id: int) -> dict:
    """Replay the original Up(3)/Down(4) cursor movement for Display_jump=1."""
    if not isinstance(world, dict) or not isinstance(cursor, dict):
        raise ValueError("world and cursor objects required")
    for flag in ("key_flag", "display_list", "display_jump", "display_text", "display_buy"):
        if type(world.get(flag)) is not int:
            raise ValueError("original keyboard gate flags required")
    if type(arrow_id) is not int or arrow_id not in (3, 4):
        raise ValueError("jump selection requires Up(3) or Down(4)")
    if world["display_jump"] != 1 or world["display_buy"] == 1:
        raise ValueError("jump menu inactive or shop modal takes precedence")
    index = cursor.get("now_move_id")
    if type(index) is not int or not 1 <= index <= 20:
        raise ValueError("original cursor index must be 1..20")
    for name in ("moves_x", "moves_y", "move_x"):
        value = cursor.get(name)
        if type(value) not in (int, float) or not isfinite(value):
            raise ValueError("finite numeric cursor coordinates required")
    state, selection = deepcopy(world), deepcopy(cursor)
    if arrow_id == 3:
        index -= 1
        if index == 0:
            index = 20
            selection["moves_y"] += 150
            selection["moves_x"] += selection["move_x"] * 2
        elif index in (7, 14):
            selection["moves_x"] -= selection["move_x"]
            selection["moves_y"] += 180
        else:
            selection["moves_y"] -= 30
    else:
        index += 1
        if index == 21:
            index = 1
            selection["moves_y"] -= 150
            selection["moves_x"] -= selection["move_x"] * 2
        elif index in (8, 15):
            selection["moves_x"] += selection["move_x"]
            selection["moves_y"] -= 180
        else:
            selection["moves_y"] += 30
    selection["now_move_id"] = index
    return {"state": state, "cursor": selection, "event": "jump_cursor_moved",
            "effects": ["play_sound:music_11"]}
