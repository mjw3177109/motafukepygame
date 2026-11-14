# Explicit arrow / text sprite replay (limited evidence)

This is a **composition of existing FFDec-verified sub-branches**, not a new claim about original timing. See `docs/arrow-turn-audit.md` and `docs/text-lifecycle-audit.md` for original SWF SHA256, source ActionScript paths, and their hashes.

`core/text_turn_replay.py` and `web/text_turn_replay.mjs` accept an ordered action list. `arrow` calls the existing input-gated movement/encounter probe. `text_frame32` explicitly calls the verified `mt_other_03` frame 32 sub-branch; `text_cleanup` explicitly calls the verified `sprite855` frame 1 text-cleanup sub-branch. The caller must observe these original frame events; the replay **does not invent elapsed frames, animation speeds, sprite scheduling, or UI rendering**.

Regression fixtures cover a key pickup blocking input until both explicit text phases finish, boss text retaining input lock, and floor 26 cell `[3][5] == 0` producing an ending **request**, not a rendered ending. After that request, the replay fails closed on further actions because the actual ending controller is not implemented. Invalid or unsupported events fail closed. Snapshots and caller inputs are not mutated.

The fixtures are constructed test inputs, not recordings of original gameplay. No original Flash side-by-side visual test, door animation, stair transition, shop, save/load, complete ending, Pygame UI, HTML5 UI, Gymnasium or Kaggle training is implemented here.
