# Tile 24 — source-gated branch-local trace (NOT Flash parity)

This increment adds `tools/trace_tile24_states.py` and `tests/test_trace_tile24_states.py` to convert four previously audited `Move_arrow` tile-24 source blocks into **review-only, deterministic input/output examples**. The tool calls `verify_tile24_branch_order()` on supplied ActionScript before tracing, rejects malformed inputs, preserves the input, and records only effects represented in the audited branch-local model. `CopyMovie` and `gotoAndPlay` are **logged as commands, not executed**.

The model follows the audited independent source order: initial dialogue → ending-state change → `my_love` dialogue → floor-22 three-item dialogue. For tile 24 with `Display_say[0]=0`, `mt_changes=1`, `my_love=0`, and floor 22, the *branch-local hypothetical* trace includes initial dialogue, `say_three`, and floor-22 `say_five`/`say_six` selection. It does **not** establish that a real Flash run reaches or executes these branches together. Other `Move_arrow` statements, movie timing, external map mutation, save/load, UI, and actual Pygame/HTML5 runtime are out of scope.

Focused regression: `python -m unittest discover -s tests -p 'test_trace_tile24_states.py' -v`. Existing CI Python discovery includes these tests. Next: capture original Flash input/state traces and compare actual Pygame and HTML5 replays, including cases where multiple guards might be true. Neither source audit nor synthetic replay authorizes 1:1 or Gymnasium/Kaggle claims.

## Shared Python/JavaScript synthetic cases (2026-11-02)

Added `web/tile24_state_probe.mjs` and nine shared fixture cases under `tests/fixtures/tile24_state_cases.json`. Python's existing source-gated review tracer and the independent JavaScript review probe must produce the same branch order, dialogue commands, and state changes for these **synthetic inputs**. Added Python fixture checks and a Node test step to CI. JavaScript explicitly returns `source_branch_order_verified: false` because it does not parse original ActionScript. Both probes return `flash_runtime_verified: false`, `dual_client_parity_verified: false`, and `gymnasium_ready: false`.

This is **cross-language probe regression**, not real Pygame/HTML5 game execution, not evidence that independent Flash `if` branches all execute during one move, and not a 1:1 parity claim. Next: obtain real Flash input/state captures, implement event handling in actual clients, and compare their traces against the original. Training remains blocked.

## Shared fixture clip-command guard (2026-11-02)

Previous shared tests checked branch names, dialogue commands, and final state, but **did not assert `CopyMovie` commands or which branch emitted them**. A regression that dropped or moved a clip command could pass both language suites. The nine synthetic fixtures now specify `clip_commands` as ordered `{branch, clip_command}` records; Python and JavaScript both compare them exactly, including empty cases and two-command combinations. This is a regression guard for *review-only command logging*, not Flash movie execution or actual client parity. No gameplay behavior, SWF resources, or RL readiness flags changed.
