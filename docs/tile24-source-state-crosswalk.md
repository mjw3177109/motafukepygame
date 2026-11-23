# Tile 24 source-to-probe field crosswalk (static evidence only)

This is a review checklist, **not** a Flash runtime capture or an implementation authorization. Source provenance: original `game.swf`, FFDec `frame_4346/DoAction_2.as` (SHA256 `0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034`), as recorded in `docs/original-say08-handoff-audit.md`; the source-guard checks are implemented in `tools/audit_tile24_branch_order.py`. Revalidate the SHA against a fresh FFDec export before using these anchors.

| Synthetic probe field | Original ActionScript expression or source evidence | Evidence status |
| --- | --- | --- |
| `tile_id` | `Number(eval(temp_lines)[temp_x][temp_y]) == 24` in four `Move_arrow` guards | Static guard only; probe value is an abstraction, not an original state variable |
| `display_say0` | `_root.Display_say[0]` read and set to 1 in dialogue guards | Static guard/write |
| `mt_changes` | `_root.mt_changes` read as 1 and set to 0 | Static guard/write |
| `my_love` | `_root.my_love` read as 0/1 and set to 0 in love branch | Static guard/write |
| `now_line` | `_root.Now_line == 22` | Static guard |
| `get_money` | `Number(_root.mt_GetMoney[0..2]) == 1` in the item-dependent branches | Static reads; array lifetime/initialization not established here |
| `now_key_flag` | `_root.Now_key_flag = 0` in floor-22 branch | Static write |
| `last_game_id` | `_root.mt_LastGame_ID = 1` in tile-24 ending branch; initialization and load paths documented in `docs/original-terminal-guard-paths-audit.md` | Static writes, **not** a proven ending |
| `floor20_7_5` | `_root.mt_line_20[7][5] = 13` in both love-dialogue arms | Static write; cell's actual runtime floor context unverified |

## Critical distinction and blocked work

The synthetic `trace_tile24_states` reads the fields as an isolated snapshot and logs `CopyMovie`/`gotoAndPlay` commands without executing them. The original `Move_arrow` source includes surrounding control flow and mutable state not represented in that snapshot. In particular, independently present `if` statements **do not prove** that all guards can be reached in one real movement turn. Do not connect the synthetic trace directly to a production Pygame or HTML5 event handler as verified original behavior.

For a genuine runtime comparison, capture the original Flash floor, hero position, input, tile value, all nine fields **before and after** each event, clip timeline/frame, and save/load state; then replay the same input in both clients. Mark mismatches separately for state, event order, dialogue, and rendering. No capture exists in this increment; all runtime, ending, and Gymnasium/Kaggle gates remain closed.

Source audit regression: `python -m unittest discover -s tests -p 'test_audit_tile24_branch_order.py' -v`. Synthetic trace regression: `python -m unittest discover -s tests -p 'test_trace_tile24_states.py' -v`. Passing either test only verifies the documented static/synthetic scope.
