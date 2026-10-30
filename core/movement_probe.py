"""Verified, deliberately incomplete subset of Flash Move_arrow.

Input is a JSON-compatible snapshot; no input mutation. This does NOT implement
input-modal gates, sprites, audio, fights, stairs, scripts, or game completion.
"""
from __future__ import annotations

from copy import deepcopy

# Flash arrow IDs, not keyboard key codes. [row, column] is mt_line[x][y].
DELTAS = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}
KEY_PICKUPS = {6: "yellow", 7: "blue", 8: "red"}
KEY_DOORS = {2: "yellow", 3: "blue", 4: "red"}
STAT_PICKUPS = {9: ("defense", 3), 10: ("attack", 3), 11: ("hp", 200), 12: ("hp", 500)}


class UnsupportedTileError(ValueError):
    """A tile has original side effects not yet implemented or verified."""


def step_move_arrow(snapshot: dict, arrow_id: int) -> dict:
    """Return {state, event} for a known tile interaction only.

    Only invoke this after the original keyboard/UI gating has accepted input.
    The caller is responsible for all animation and modal completion.
    """
    if type(arrow_id) is not int or arrow_id not in DELTAS:
        raise ValueError("arrow_id must be one of Flash 1,2,3,4")
    state = deepcopy(snapshot)
    grid = state["grid"]
    if len(grid) != 11 or any(len(row) != 11 for row in grid):
        raise ValueError("expected 11x11 original floor")
    row, col = state["row"], state["col"]
    if not (type(row) is int and type(col) is int and 0 <= row < 11 and 0 <= col < 11):
        raise ValueError("invalid original row/column")
    dr, dc = DELTAS[arrow_id]
    nr, nc = row + dr, col + dc
    if not (0 <= nr < 11 and 0 <= nc < 11):
        return {"state": state, "event": "boundary"}
    tile = grid[nr][nc]
    if type(tile) is not int:
        raise ValueError("tile must be an integer")
    if tile == 0:
        state["row"], state["col"] = nr, nc
        return {"state": state, "event": "move"}
    if tile == 1:
        return {"state": state, "event": "wall"}
    if tile in KEY_PICKUPS:
        key = KEY_PICKUPS[tile]
        state["keys"][key] += 1
        grid[nr][nc] = 0
        return {"state": state, "event": "pickup_" + key + "_key"}
    if tile in KEY_DOORS:
        key = KEY_DOORS[tile]
        if state["keys"][key] == 0:
            return {"state": state, "event": "locked_" + key + "_door"}
        state["keys"][key] -= 1
        grid[nr][nc] = 0
        return {"state": state, "event": "open_" + key + "_door"}
    if tile in STAT_PICKUPS:
        stat, amount = STAT_PICKUPS[tile]
        state[stat] += amount
        grid[nr][nc] = 0
        return {"state": state, "event": "pickup_" + stat + "_" + str(amount)}
    raise UnsupportedTileError(f"tile {tile} needs original event/animation verification")
