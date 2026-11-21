"""Read-only Flash Move_arrow encounter gate, not a combat simulator.

Provenance: game.swf -> frame_4346/DoAction_2.as, Move_arrow monster branch.
No animation, HP mutation, gold, experience, monster death, or victory here.
"""
from __future__ import annotations


def preview_encounter(tile: int, monster: list, hero: dict) -> dict:
    """Reproduce the original *entry gate* arithmetic for one monster tile.

    `monster` is the raw boss_man[id] array from original_tables.json.
    `hero` requires integer hp, attack and defense. Returns no modified state.
    """
    if type(tile) is not int or not (40 <= tile <= 70 or tile in (188, 198)):
        raise ValueError("unsupported original monster tile")
    enemy_id = (31 if tile == 188 else 32 if tile == 198 else tile - 40)
    if not isinstance(monster, list) or len(monster) != 6 or any(type(v) is not int for v in monster[:5]) or not isinstance(monster[5], str):
        raise ValueError("expected raw six-field original boss_man array")
    if not isinstance(hero, dict) or any(type(hero.get(k)) is not int for k in ("hp", "attack", "defense")):
        raise ValueError("hero must contain integer hp, attack and defense")
    enemy_hp, enemy_attack, enemy_defense = monster[:3]
    if hero["attack"] <= enemy_defense:
        return {"enemy_id": enemy_id, "can_start": False, "reason": "insufficient_attack", "base_loss": None, "special_loss": None, "estimated_loss": None}
    # ActionScript int() truncates toward zero, not ceil() and not Python //.
    base_loss = int(enemy_hp / (hero["attack"] - enemy_defense)) * (enemy_attack - hero["defense"])
    special_loss = {20: 100, 12: 300, 10: int(hero["hp"] / 4), 17: int(hero["hp"] / 3)}.get(enemy_id, 0)
    loss = base_loss + special_loss
    can_start = loss <= hero["hp"]  # Original blocks only when tmp_kills > Now_hp.
    return {"enemy_id": enemy_id, "can_start": can_start, "reason": "ok" if can_start else "insufficient_hp", "base_loss": base_loss, "special_loss": special_loss, "estimated_loss": loss}
