# Text completion: verified narrow original Flash sub-branches

Source: `game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`, exported using FFDec/Java 8.

- `export/scripts/DefineSprite_433_mt_other_03/frame_32/DoAction.as`, SHA256 `2535f2a4f402a79bb2c05c21aa0b716be8553d6b605fd48e7487409161074906`: if `Number(_root.boss_kills)==1`, set `Now_key_flag=0`; otherwise set it to `1`. Then set `Display_text=2`.
- `export/scripts/DefineSprite_855/frame_1/DoAction.as`, SHA256 `3c6de7a67bd0e02e57438ec13cbcd081f1a5487a981e1bb960f2e0872bdddb38`: when `Display_text==2`, remove `mt_display_text`, set `Display_text=0`; if `Number(mt_line_26[3][5])==0`, clear base and floor displays and request `game_over`. The cleanup branch does **not** change `Now_key_flag`.
- `export/scripts/frame_4346/DoAction.as` initial floor 26 row 3 column 5 is `188`, **not** zero. This initial value is not a guarantee about runtime progression.

`core/text_lifecycle_probe.py` and `web/text_lifecycle_probe.mjs` model these **two sub-branches only**. Call `frame32` only after the text sprite reaches its actual frame 32; call `cleanup` only when sprite 855 reaches frame 1 and the floor 26 cell is explicitly known. Do not automatically advance animation frames or infer the floor 26 cell from the active floor. `game_over_requested` is an effect request, not proof that a complete ending has been rendered. Other sprite855 branches (door cleanup, battles, dialogs, stairs, shop, save/load) are **not** emulated. Synthetic fixtures are not captured Flash playthroughs. Kaggle/Gymnasium remains gated.
