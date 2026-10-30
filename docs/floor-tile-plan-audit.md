# SetLineDisplay(1) full floor snapshot and static tile placement

Evidence: `game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`; FFDec Java 8 export artifact `12952870432` (run `40998902161`). Source maps `export/scripts/frame_4346/DoAction.as` SHA256 `2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c`; renderer `export/scripts/frame_4346/DoAction_2.as` SHA256 `0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034`.

`data/original_floors.json` preserves **all 27 original 11×11 initial floor matrices**, including non-marker tiles and original `[row][column]` index order. It was copied from the FFDec artifact `original_tables.json`, without invented tile IDs or map layouts. These are *initial* arrays, not dynamically updated gameplay state. Existing marker fixture remains an independent cross-check of tile 97/98/99 positions.

`SetLineDisplay(1)` iterates rows then columns, skips tile 0 and tile 98, maps tile 97 to `mt_man` sourced from `mt_99` at depth 1000, and otherwise uses `mt_m_{row}_{col}` at depth `500 + (row+1)*11 + col+1` (special tile 24 uses `mt_sister`). Source aliases: tiles 1..9 -> `mt_01`..`mt_09`; 115 -> `mt_15`; 120 -> `mt_20`; 119/129/139/149/159/169/179 -> `mt_00`; others -> `mt_{tile}`. Position is `(207+32*column, 47+32*row)`. Tiles 1..5, 15 and 115 receive `gotoAndStop(1)` after copy.

Python `core/floor_tile_plan.py` and JS `web/floor_tile_plan.mjs` compute **static placement instructions only**. They do not execute Flash CopyMovie, play BGM, draw images, apply tile collision or dynamic events, restore input, or prove runtime parity. Both explicitly preserve `floor_refresh_pending` and do not authorize keyboard unlock. Floor 00 has no tile 97, so this jump-specific planner refuses it; original entry behavior uses a different `arrow_id` branch. Rejecting malformed or duplicate 97 is a port validation policy, not an assertion that Flash throws.

Next: connect these plans to actual Pygame and Canvas renderers, verify source assets and layer order, and compare original Flash screenshots and event traces before removing any input guard. RL/Kaggle gate remains closed.
