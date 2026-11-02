"""Deterministic *one-frame* probe of original mt_other_04 fight animation.

Evidence: FFDec export of game.swf, DefineSprite_453_mt_other_04
frame_1, frame_24, frame_34 and frame_54. Not a complete battle engine.
"""
from __future__ import annotations

from copy import deepcopy

_FIELDS = ("left_hp", "left_gong", "left_fang", "right_hp", "right_gong",
           "right_fang", "life", "kill_left", "kill_right", "kill_number")


def begin_battle(monster: list, hero: dict, life: int) -> dict:
    """Mirror sprite frame 1: left=monster, right=hero, hero attacks first.

    The caller must separately check original encounter entry conditions and
    apply any special immediate damage from Move_arrow before calling this.
    """
    if not isinstance(monster, list) or len(monster) != 6 or any(type(v) is not int for v in monster[:5]) or not isinstance(monster[5], str):
        raise ValueError("expected raw six-field boss_man entry")
    if not isinstance(hero, dict) or any(type(hero.get(k)) is not int for k in ("hp", "attack", "defense")):
        raise ValueError("hero requires integer hp, attack and defense")
    if type(life) is not int or life < 0:
        raise ValueError("life must be a nonnegative integer")
    left_hp, left_gong, left_fang = monster[:3]
    right_hp, right_gong, right_fang = hero["hp"], hero["attack"], hero["defense"]
    return {"left_hp": left_hp, "left_gong": left_gong, "left_fang": left_fang,
            "right_hp": right_hp, "right_gong": right_gong, "right_fang": right_fang,
            "life": life, "kill_left": max(0, left_gong - right_fang),
            "kill_right": max(0, right_gong - left_fang), "kill_number": 0}


def step_battle_frame(snapshot: dict, critical_roll: int | None = None) -> dict:
    """Mirror *one execution* of sprite frame 24 with supplied Flash random(200).

    A roll (0..199) is required on the hero's even-numbered attack only. The
    original's frame-34 loop and frame-35/54 transition are intentionally not
    simulated. jump_to_35 reports the exact frame-24 gotoAndPlay condition.
    """
    if not isinstance(snapshot, dict) or any(type(snapshot.get(k)) is not int for k in _FIELDS):
        raise ValueError("battle snapshot requires integer original fields")
    if snapshot["kill_number"] < 0 or snapshot["life"] < 0 or snapshot["kill_left"] < 0 or snapshot["kill_right"] < 0:
        raise ValueError("invalid battle counters or damage")
    state = deepcopy(snapshot)
    if not (state["left_hp"] > 0 or state["right_hp"] > 0):
        if critical_roll is not None:
            raise ValueError("idle frame does not consume a random roll")
        return {"state": state, "event": "idle", "damage": 0, "critical": None, "jump_to_35": False}
    if state["kill_number"] % 2 == 0:
        if type(critical_roll) is not int or not 0 <= critical_roll < 200:
            raise ValueError("hero attack requires Flash random(200) result in 0..199")
        critical = critical_roll <= state["life"]
        damage = state["kill_right"] * (2 if critical else 1)
        state["left_hp"] = max(0, state["left_hp"] - damage)
        event, jump = "hero_attack", False
    else:
        if critical_roll is not None:
            raise ValueError("monster counterattack must not consume a random roll")
        damage, critical = state["kill_left"], None
        state["right_hp"] -= damage  # Original does not clamp hero HP to zero.
        event, jump = "monster_counterattack", state["left_hp"] == 0
    state["kill_number"] += 1
    return {"state": state, "event": event, "damage": damage,
            "critical": critical, "jump_to_35": jump}
