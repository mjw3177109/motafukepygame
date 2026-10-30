"""Evidence-scoped frame54 -> sprite855 -> Move_arrow(100) settlement probe.

Does not simulate battle animation, death, modal close, or final victory.
"""
from copy import deepcopy


def _integer(value):
    return type(value) is int


def frame54_handoff(world: dict, battle: dict) -> dict:
    """Sprite mt_other_04 frame54: Display_kill=2 and Now_hp=right_hp."""
    if not isinstance(world, dict) or world.get("display_kill") != 1 or not _integer(world.get("hp")):
        raise ValueError("frame54 requires an active battle (display_kill=1)")
    if not isinstance(battle, dict) or not _integer(battle.get("right_hp")) or battle.get("left_hp") != 0:
        raise ValueError("frame54 requires a completed monster animation")
    state = deepcopy(world)
    state["display_kill"] = 2
    state["hp"] = battle["right_hp"]  # May be negative in original.
    return {"state": state, "event": "frame54_handoff"}


def consume_battle_completion(world: dict, monster: list) -> dict:
    """Sprite855 consumes Display_kill=2, then Move_arrow(100) grants rewards.

    Boss ids 31/32 clear a 3x3 region [boss_row-2..boss_row,
    boss_col-1..boss_col+1]; ordinary enemies clear one grid cell.
    """
    if not isinstance(world, dict) or world.get("display_kill") != 2:
        raise ValueError("battle settlement requires display_kill=2")
    if not isinstance(monster, list) or len(monster) != 6 or any(not _integer(v) for v in monster[:5]) or not isinstance(monster[5], str):
        raise ValueError("expected original six-field boss_man entry")
    if any(not _integer(world.get(k)) for k in ("boss_id", "boss_row", "boss_col", "hp", "money", "mp")):
        raise ValueError("invalid battle settlement state")
    boss_id, row, col = (world[k] for k in ("boss_id", "boss_row", "boss_col"))
    if not 0 <= boss_id <= 32 or not (0 <= row < 11 and 0 <= col < 11):
        raise ValueError("invalid original monster id or coordinates")
    grid = world.get("grid")
    if not isinstance(grid, list) or len(grid) != 11 or any(not isinstance(line, list) or len(line) != 11 or any(not _integer(tile) for tile in line) for line in grid):
        raise ValueError("expected 11x11 integer grid")
    cells = ([[r, c] for r in range(row - 2, row + 1) for c in range(col - 1, col + 2)]
             if boss_id in (31, 32) else [[row, col]])
    if any(not (0 <= r < 11 and 0 <= c < 11) for r, c in cells):
        raise ValueError("boss footprint outside original 11x11 floor")
    state = deepcopy(world)
    state["display_kill"] = 0
    state["display_text"] = 1
    for r, c in cells:
        state["grid"][r][c] = 0
    state["money"] += monster[3]
    state["mp"] += monster[4]
    return {"state": state, "event": "battle_reward", "cleared": cells,
            "removed_clips": [f"mt_m_{r}_{c}" for r, c in cells],
            "message": f"得到金币数 {monster[3]} 经验值 {monster[4]} ！",
            "sound": "music_03"}
