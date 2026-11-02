# Original Flash 1.12 arrow input gate / deterministic turn router

Source: game.swf SHA256 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9, FFDec/Java 8 exports.
Verified ActionScript SHA256: frame_4346/DoAction_2.as = 0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034.
Original button handlers (DefineButton2_856): Left 5f9c3b7e0efbd9487368e28714ebf7e25c7d4505fa8619af0ca8b9b5d67c3392; Right 2ac9f2e928da3e4e2cf31f4c7962917f098e8589cbd8f0944d322f98f3a4461d; Up 9c583c7f5a72caf1a2be23a4c3a41bc095c4e51905c1873ff529f0676ed23dd5; Down 806d8eb01893d30709533d291254619ba66d272bca55ee2777c1db3bfbe4a3fb.

All four arrow handlers call Move_arrow(1/2/3/4) only when Now_key_flag == 1 and Display_list == 0 and Display_jump == 0 and Display_text == 0. Up/down otherwise prioritize Display_buy == 1 then Display_jump == 1, where the original manipulates modal selections. Left/right have no such branches in these four handlers. Unsupported modal navigation fails closed rather than pretending to be a normal movement.

The new core/arrow_turn_probe.py and web/arrow_turn_probe.mjs compose the existing movement and encounter probes. Key, gem and potion pickups apply original Now_key_flag=0 / Display_text=1 side effects. Successful door opening applies Now_key_flag=0 / Open_room=1 and Last_x/Last_y. Monster encounters use the verified encounter pipeline, including explicit critical-roll input and reward text. Non-monster input cannot consume combat rolls.

Replays record state snapshots but never synthesize modal completion. The original text frame32 and sprite855 cleanup, door animation, menus, stairs, save/load, graphics, sound, death and ending remain unimplemented. The hero values and rolls in test fixtures are synthetic test inputs, not original Flash gameplay captures. Passing these tests does not prove complete Pygame/HTML5 1:1 parity. Gymnasium/Kaggle remains gated until full evidence-based signoff.

## 2026-11-02: JavaScript 11×11 grid integrity guard

The HTML5-side movement and arrow-turn probes previously used `Array.prototype.some/every` for grid validation. These skip sparse array holes, so a missing row or cell could pass the preflight (including a value inherited through an array prototype). This creates a real cross-language input-validation gap before any tile-24 event can safely be integrated.

Both JavaScript probes now share `isDenseOriginalGrid`, requiring all 121 cells and all 11 rows to be **own** array indices with safe-integer values. New tests reject missing rows, missing cells, inherited cells, and unsafe integers without mutating the input. Python lists cannot represent JavaScript array holes, so no Python gameplay rule is changed. This is a **fail-closed preflight correction**, not an original Flash gameplay event implementation or 1:1 verification. Tile 24 still fails closed in the movement router; original Flash runtime evidence and actual Pygame/HTML5 event wiring are pending.

## 2026-11-02: Python arrow-router JSON-safe preflight parity

The Python router accepted out-of-range integer keyboard flags and non-target map cells that the JavaScript router rejected with `Number.isSafeInteger`. It also treated `display_kill=False` as idle because Python compares `False == 0`. The Python router now rejects non-JSON-safe integers in every keyboard gate flag and all 121 grid cells, and requires an actual integer zero for the idle battle flag. Regression tests include untouched input checks and JS-side contract checks. These guards prevent silent cross-runtime divergence; they do not establish Flash runtime parity, implement tile-24 gameplay events, or authorize Gymnasium/Kaggle.

## 2026-11-02: Standalone Python Move_arrow grid preflight parity

The Python `step_move_arrow` probe could accept a boolean, float, string or integer outside JavaScript's safe-integer range in a **non-target** grid cell, because it checked only the 11x11 dimensions and then the target tile type. It also accepted tuple/dict rows that the HTML5 `isDenseOriginalGrid` rejects. The arrow-turn composition had already added a stronger guard, but direct calls to the standalone movement probe still diverged from the JavaScript counterpart.

The standalone Python probe now requires a real list of 11 real list rows, with all 121 cells exactly `int` and within ±(2^53−1). Two regression methods reject non-target malformed values and non-list containers while asserting no input mutation. This is a **cross-language input preflight correction only**, not a new Flash tile handler, not Pygame/HTML5 gameplay parity and not a reason to open the Gymnasium/Kaggle gate. Tile 24 still requires a source-verified runtime event handoff and original Flash capture.

## 2026-11-02: HTML5 arrow keyboard flags must be own properties

The JavaScript `classifyArrowInput` previously read inherited flag values from an object's prototype and even accepted an Array with ad-hoc flag properties. Python's `dict.get` does not read JavaScript prototype properties, so a malformed cross-runtime snapshot could enter `move_arrow` in HTML5 while Python rejects it. The five original keyboard flags now require own safe-integer properties on a non-array object. Regression tests cover each inherited flag and an array-shaped world through both the gate and turn router. An isolated Node.js gate regression passed before the change was submitted; repository CI is the authoritative integration test. This is a fail-closed input validation correction, **not** original Flash runtime parity or tile-24 event wiring. Gymnasium/Kaggle remains blocked.

## 2026-11-02: Key inventory type and overflow guard (movement subset)

Before this change, JS `state.keys[color]++` silently coerced strings/booleans and could round values above the JSON-safe integer boundary. Python accepted `True` as an integer count and could increment a count beyond the JS safe range. Both standalone movement probes now require own (JS) safe-integer counts for yellow, blue and red keys before movement and reject pickup overflow without modifying the input. Existing source-review fixture `yellow_door_negative_keys` remains valid: negative inventory is deliberately **not** prohibited without original-source proof. Regression cases cover missing, inherited, coerced and oversized values plus overflow. This only hardens deterministic movement input; it does not implement tile 24, resolve Flash dynamic parity or authorize RL.
