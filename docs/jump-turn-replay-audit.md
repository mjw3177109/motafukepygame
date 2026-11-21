# Floor-jump menu event replay (limited composition, not floor redraw)

Source: original `game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9` and FFDec/Java 8 export from GitHub Actions run `40998902161` (artifact `original-flash-audit`, ID `12952870432`).

This patch **does not claim new original ActionScript extraction**. It composes the already evidenced `jump_selection_probe` and `jump_lifecycle_probe` rules. Source script paths and hashes are in [`jump-selection-audit.md`](jump-selection-audit.md) and [`jump-lifecycle-audit.md`](jump-lifecycle-audit.md).

The Python/JS replay accepts explicit `up`, `down`, `confirm`, `cancel`, and `cleanup` events and records immutable step snapshots. Confirmed jumps retain the keyboard lock after sprite855 cleanup and expose `floor_refresh_pending=true` when `SetLineDisplay(1)` is requested. The runner **refuses further actions** rather than inventing the missing floor rendering, hero placement, or unlock timing. Cancellation clears the modal and restores the keyboard according to the existing lifecycle probe. A rejected target still follows the original confirmation cleanup request.

Shared fixtures cover selection wrap, accepted/rejected confirmation, cancellation from menu and sprite state 3, premature cleanup, invalid action payloads, and shop priority. Coordinates and worlds are synthetic; passing tests only establish parity between these isolated extracted rules, **not** original runtime frame timing, complete map/event parity, or Pygame/HTML5 visual parity.

Next evidence gate: inspect `SetLineDisplay(1)` and related frame/event scripts in the FFDec artifact; obtain an original runtime trace of map redraw, hero spawn, and input restoration before adding any such behavior. Gymnasium/Kaggle remains blocked until full game, maps, and endings pass automated and human parity review.
