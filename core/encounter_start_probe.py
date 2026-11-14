"""Evidence-scoped Move_arrow monster encounter -> mt_other_04 frame-1 handoff.

No sprite/audio execution, fight-frame loop, reward, or victory logic. The
caller must first apply the original keyboard/modal input gate.
"""
from __future__ import annotations

from copy import deepcopy

from core.combat_probe import preview_encounter
from core.battle_frame_probe import begin_battle

DIRECTIONS = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}
SPECIAL_SOUNDS = {20: "music_20", 12: "music_24", 10: "music_22", 17: "music_23"}


def start_encounter(world: dict, arrow_id: int, monsters: dict) -> dict:
    """Return {state,event,sound,preview,battle} without mutating inputs.

    `monsters` is the exact ID-keyed original_tables.json `monsters` object.
    On rejection, original boss 19's early flag side effect still occurs.
    """
    if type(arrow_id) is not int or arrow_id not in DIRECTIONS:
        raise ValueError("expected original Flash arrow id 1..4")
    if not isinstance(world, dict) or any(type(world.get(k)) is not int for k in ("row", "col", "hp", "attack", "defense", "life", "line")):
        raise ValueError("invalid original encounter state")
    row, col = world["row"], world["col"]
    if not (0 <= row < 11 and 0 <= col < 11):
        raise ValueError("invalid original coordinates")
    grid = world.get("grid")
    if not isinstance(grid, list) or len(grid) != 11 or any(not isinstance(r, list) or len(r) != 11 or any(type(v) is not int for v in r) for r in grid):
        raise ValueError("expected original 11x11 integer grid")
    dr, dc = DIRECTIONS[arrow_id]
    nr, nc = row + dr, col + dc
    if not (0 <= nr < 11 and 0 <= nc < 11):
        raise ValueError("encounter target outside floor")
    tile = grid[nr][nc]
    enemy_id = 31 if tile == 188 else 32 if tile == 198 else tile - 40
    if not (40 <= tile <= 70 or tile in (188, 198)):
        raise ValueError("target is not an original monster tile")
    if not isinstance(monsters, dict) or str(enemy_id) not in monsters:
        raise ValueError("missing verified monster entry")
    monster = monsters[str(enemy_id)]
    preview = preview_encounter(tile, monster, world)
    state = deepcopy(world)
    # Move_arrow sets this before the encounter gate, even if entry is denied.
    if enemy_id == 19 and state["line"] < 22:
        state["boss_kills"] = 1
    if not preview["can_start"]:
        return {"state": state, "event": "encounter_blocked", "sound": "music_10", "preview": preview, "battle": None}
    # Original special damage occurs *after* the gate and *before* frame 1.
    state["hp"] -= preview["special_loss"]
    state["boss_id"] = enemy_id
    state["boss_row"], state["boss_col"] = nr, nc
    state["key_flag"] = 0
    state["display_kill"] = 1
    battle = begin_battle(monster, state, state["life"])
    return {"state": state, "event": "encounter_started", "sound": SPECIAL_SOUNDS.get(enemy_id), "preview": preview, "battle": battle}
