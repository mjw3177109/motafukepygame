# Flash 1.12 floor-jump confirmation, cancellation and cleanup — narrow parity probe

Original `game.swf` SHA256: `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`.
FFDec Java 8 export: Actions run `40998902161`, artifact `original-flash-audit` ID `12952870432`.

Original ActionScript evidence (SHA256 of exported script bytes):

- `export/scripts/DefineButton2_718/BUTTONCONDACTION on(keyPress Space).as`: `377025e9f771f4c101669cbee4493922eb112c61376e664197426a65defe7264`
- `export/scripts/DefineButton2_718/BUTTONCONDACTION on(keyPress 5).as`: `9a3ce01a07f0528c1164771c265ff168c9eb1c1058d07101f381b10bcb7baf1c`
- `export/scripts/DefineButton2_718/BUTTONCONDACTION on(keyPress J).as`: `8fd78d8344c828f0982490337114baf7d35ec0e94bf27fc1c30c06c53fa92698`
- `export/scripts/DefineButton2_856/BUTTONCONDACTION on(keyPress J).as`: `16811d10456a797faf80296b3ce5fdc3d0e34718e7a443dbbf28c75190b1082d`
- `export/scripts/DefineSprite_855/frame_1/DoAction.as`: `3c6de7a67bd0e02e57438ec13cbcd081f1a5487a981e1bb960f2e0872bdddb38`
- `export/scripts/DefineSprite_720_mt_jump/frame_1/DoAction.as`: `485e50d27e122a31acd9a663dec711f2896be62333982513971caa85b3a4357a`

Observed rules: Space/5 on the menu sets `Display_jump=2` regardless of whether the selected floor is valid. The original accepts only `now_move_id < Max_line` (strictly less), then calls `DelLineDisplay`, changes `Now_line`, and plays `music_07`; otherwise it plays `music_10` without changing floors. Sprite855 cleanup of state 2 removes `mt_line_jump`, calls `SetLineDisplay(1)`, resets `Display_jump=0`, and leaves `Now_key_flag=0`. Menu J sets state 4 and `Now_key_flag=1`; global J from state 3 sets state 4 without directly changing the key flag. Sprite855 cleanup of state 4 removes the menu and restores `Now_key_flag=1`.

The Python and JS probes reproduce **only these recorded assignments and effect requests**. They do not render floors, simulate `SetLineDisplay`, prove when menu state 1 becomes state 3, reproduce frame timing, or validate hero placement. The shared test worlds are synthetic. Do not claim complete jump-menu or full-game 1:1 parity, or authorize Gymnasium/Kaggle training from these tests.
