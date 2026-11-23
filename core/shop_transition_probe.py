"""Static-ActionScript-backed shop transition probe; NOT Flash runtime parity.

Pure state transitions only. No UI, keyboard routing, or animation is claimed.
"""
from copy import deepcopy

MAX_SAFE_INTEGER = (1 << 53) - 1
# Source: data/original_shop_transactions_static.json, DefineSprite_671_mt_buy.
TRANSACTIONS = {
    (2, 1): (25, "hp", 800),
    (2, 2): (25, "attack", 4),
    (2, 3): (25, "defense", 4),
    (4, 1): (10, "yellow_key", 1),
    (4, 2): (50, "blue_key", 1),
    (4, 3): (100, "red_key", 1),
}
EXITS = {2: "gotoAndPlay", 4: "gotoAndStop"}
FIELDS = ("gold", "hp", "attack", "defense", "yellow_key", "blue_key", "red_key")


def step_shop(state: dict, frame: int, option: int) -> dict:
    """Return a new state and source-scoped event; reject unsupported input."""
    if type(frame) is not int or type(option) is not int:
        raise ValueError("frame and option must be integers")
    if frame not in EXITS or option not in (1, 2, 3, 4):
        raise ValueError("unsupported source-backed shop frame/option")
    if not isinstance(state, dict) or any(
        type(state.get(k)) is not int or not (0 <= state[k] <= MAX_SAFE_INTEGER)
        for k in FIELDS
    ):
        raise ValueError("shop requires nonnegative safe integer state fields")
    after = deepcopy(state)
    if option == 4:
        return {"state": after, "success": True, "event": "shop_exit",
                "sound": "music_07", "exit_action": EXITS[frame], "exit_label": "end",
                "provenance": "static_actionscript_expectation_not_runtime"}
    cost, field, delta = TRANSACTIONS[(frame, option)]
    if after["gold"] < cost:
        event, success, sound = "shop_insufficient_gold", False, "music_09"
    else:
        if after[field] > MAX_SAFE_INTEGER - delta:
            raise ValueError("shop stat overflow")
        after["gold"] -= cost
        after[field] += delta
        event, success, sound = "shop_purchase", True, "music_11"
    return {"state": after, "success": success, "event": event, "sound": sound,
            "provenance": "static_actionscript_expectation_not_runtime"}
