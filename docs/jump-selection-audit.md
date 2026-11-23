# Flash 1.12 floor-jump selection: narrow Up/Down parity probe

Original game.swf SHA256: 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9.
FFDec/Java 8 export: GitHub Actions run 40998902161, artifact original-flash-audit ID 12952870432.

Original scripts:

- export/scripts/DefineButton2_856/BUTTONCONDACTION on(keyPress Up).as SHA256 9c583c7f5a72caf1a2be23a4c3a41bc095c4e51905c1873ff529f0676ed23dd5
- export/scripts/DefineButton2_856/BUTTONCONDACTION on(keyPress Down).as SHA256 806d8eb01893d30709533d291254619ba66d272bca55ee2777c1db3bfbe4a3fb
- Equivalent 8 and 2 navigation in DefineButton2_718.

When ordinary movement is blocked, original Up/Down handlers prioritize Display_buy==1 over Display_jump==1. With Display_jump==1, Up decrements now_move_id (1 wraps to 20), Down increments (20 wraps to 1). Crossing 8/15 (Down) or 7/14 (Up) changes column moves._x by move_x and moves._y by 180 pixels; ordinary steps change Y by 30; wraps shift X by 2*move_x and Y by 150. Each cursor move calls PlaySound("music_11").

core/jump_selection_probe.py and web/jump_selection_probe.mjs implement only these exact cursor updates, with shared synthetic vectors. They do NOT move the hero, change floors, advance animation frames, or implement Display_jump open/confirm/cancel/cleanup. In particular, DefineSprite_720_mt_jump/frame_1/DoAction.as sets Display_jump=3; its timing relative to menu initialization still requires Flash runtime evidence. Until resolved, no complete jump-menu parity is claimed.

The tests use synthetic starting coordinates (moves_x=120, moves_y=200, move_x=40); these are test values, NOT claimed original positions. Do not interpret passing probe tests as a complete game or Gymnasium/Kaggle approval.
