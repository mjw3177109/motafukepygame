"""Evidence-scoped composition of existing encounter, battle and reward probes.

This is a deterministic *test harness*, not an interactive game or Flash
frame-timing emulator. A supplied list of Flash random(200) rolls is required.
"""
from __future__ import annotations

from core.encounter_start_probe import start_encounter
from core.battle_timeline_probe import replay_to_victory
from core.battle_settlement_probe import frame54_handoff, consume_battle_completion


def resolve_encounter(world: dict, arrow_id: int, monsters: dict,
                      critical_rolls: list, max_actions: int = 10000) -> dict:
    """Compose verified transitions without changing the caller's world."""
    if not isinstance(world, dict) or world.get("display_kill") != 0:
        raise ValueError("pipeline requires idle display_kill=0; input gate remains unverified")
    if not isinstance(critical_rolls, list):
        raise ValueError("critical_rolls must be an explicit list")
    start = start_encounter(world, arrow_id, monsters)
    events = [{"stage": "encounter", "event": start["event"], "sound": start["sound"]}]
    if start["event"] == "encounter_blocked":
        if critical_rolls:
            raise ValueError("blocked encounter cannot consume critical rolls")
        return {"state": start["state"], "events": events, "preview": start["preview"],
                "battle": None, "steps": [], "cleared": []}
    replay = replay_to_victory(start["battle"], critical_rolls, max_actions)
    events.append({"stage": "battle", "event": "frame35_reached",
                   "actions": len(replay["steps"]), "rolls_used": replay["rolls_used"]})
    handoff = frame54_handoff(start["state"], replay["battle"])
    events.append({"stage": "handoff", "event": handoff["event"]})
    monster = monsters[str(start["preview"]["enemy_id"])]
    reward = consume_battle_completion(handoff["state"], monster)
    events.append({"stage": "settlement", "event": reward["event"], "sound": reward["sound"]})
    return {"state": reward["state"], "events": events, "preview": start["preview"],
            "battle": replay["battle"], "steps": replay["steps"], "cleared": reward["cleared"]}
