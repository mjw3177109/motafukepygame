"""Deterministic Flash frame24 -> frame34 -> frame35 transition probe.

Not a wall-clock animation, complete battle engine, or original-player replay.
Critical rolls are supplied explicitly; no RNG or game rules are invented.
"""
from __future__ import annotations

from copy import deepcopy

from core.battle_frame_probe import step_battle_frame


def replay_to_victory(initial_battle: dict, critical_rolls: list, max_actions: int = 10000) -> dict:
    """Execute frame24 actions and the original frame34 loop condition.

    frame34: if (left_hp > 0) gotoAndPlay(24); otherwise advance to frame35.
    Thus a killing hero attack does NOT automatically get a final retaliation.
    This probe stops at frame35; frame54 and rewards remain separate transitions.
    """
    if not isinstance(initial_battle, dict) or initial_battle.get("kill_number") != 0:
        raise ValueError("requires a fresh frame1 battle snapshot")
    if type(initial_battle.get("left_hp")) is not int or initial_battle["left_hp"] <= 0:
        raise ValueError("requires a living original monster")
    if type(initial_battle.get("kill_right")) is not int or initial_battle["kill_right"] <= 0:
        raise ValueError("requires positive verified hero damage")
    if type(max_actions) is not int or max_actions <= 0:
        raise ValueError("max_actions must be a positive integer")
    if not isinstance(critical_rolls, list) or any(type(v) is not int or not 0 <= v < 200 for v in critical_rolls):
        raise ValueError("critical_rolls must be a list of Flash random(200) results")
    battle = deepcopy(initial_battle)
    steps = []
    rolls_used = 0
    for _ in range(max_actions):
        roll = None
        if battle["kill_number"] % 2 == 0:
            if rolls_used >= len(critical_rolls):
                raise ValueError("missing a required original critical roll")
            roll = critical_rolls[rolls_used]
            rolls_used += 1
        result = step_battle_frame(battle, roll)
        if result["event"] == "idle":
            raise ValueError("battle stalled before frame35")
        battle = result["state"]
        transition = ("frame24_to_35" if result["jump_to_35"]
                      else "frame34_to_24" if battle["left_hp"] > 0
                      else "frame34_to_35")
        steps.append({"event": result["event"], "damage": result["damage"],
                      "critical": result["critical"], "left_hp": battle["left_hp"],
                      "right_hp": battle["right_hp"], "transition": transition})
        if transition != "frame34_to_24":
            break
    else:
        raise ValueError("battle did not reach frame35 within max_actions")
    if rolls_used != len(critical_rolls):
        raise ValueError("unused critical rolls; exact replay evidence required")
    return {"battle": battle, "steps": steps, "rolls_used": rolls_used,
            "next_frame": 35}
