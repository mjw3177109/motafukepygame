# Original Flash 1.12 arrow input gate / deterministic turn router

Source: game.swf SHA256 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9, FFDec/Java 8 exports.
Verified ActionScript SHA256: frame_4346/DoAction_2.as = 0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034.
Original button handlers (DefineButton2_856): Left 5f9c3b7e0efbd9487368e28714ebf7e25c7d4505fa8619af0ca8b9b5d67c3392; Right 2ac9f2e928da3e4e2cf31f4c7962917f098e8589cbd8f0944d322f98f3a4461d; Up 9c583c7f5a72caf1a2be23a4c3a41bc095c4e51905c1873ff529f0676ed23dd5; Down 806d8eb01893d30709533d291254619ba66d272bca55ee2777c1db3bfbe4a3fb.

All four arrow handlers call Move_arrow(1/2/3/4) only when Now_key_flag == 1 and Display_list == 0 and Display_jump == 0 and Display_text == 0. Up/down otherwise prioritize Display_buy == 1 then Display_jump == 1, where the original manipulates modal selections. Left/right have no such branches in these four handlers. Unsupported modal navigation fails closed rather than pretending to be a normal movement.

The new core/arrow_turn_probe.py and web/arrow_turn_probe.mjs compose the existing movement and encounter probes. Key, gem and potion pickups apply original Now_key_flag=0 / Display_text=1 side effects. Successful door opening applies Now_key_flag=0 / Open_room=1 and Last_x/Last_y. Monster encounters use the verified encounter pipeline, including explicit critical-roll input and reward text. Non-monster input cannot consume combat rolls.

Replays record state snapshots but never synthesize modal completion. The original text frame32 and sprite855 cleanup, door animation, menus, stairs, save/load, graphics, sound, death and ending remain unimplemented. The hero values and rolls in test fixtures are synthetic test inputs, not original Flash gameplay captures. Passing these tests does not prove complete Pygame/HTML5 1:1 parity. Gymnasium/Kaggle remains gated until full evidence-based signoff.
