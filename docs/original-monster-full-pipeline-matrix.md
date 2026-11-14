# Full original-monster battle pipeline regression (not Flash gameplay parity)

Source: `game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`.
All 33 `boss_man` entries are taken from `data/original_combat_tables.json`; the SWF, FFDec ActionScript declarations, and field semantics are checked by existing independent CI audits.

## This increment

Prior coverage checked 132 encounter *entry estimates* in each runtime, but only four fixture scenarios traversed the composed battle/reward pipeline. New Python and Node regressions exercise all 33 monster IDs in two deterministic scenarios (66 scenarios per runtime, 132 total):

- One-hit hero victory with no monster retaliation.
- Two-hit victory with exactly one seven-HP monster counterattack.

The test heroes have 1,000,000 initial HP, attacks derived from each source monster's HP/defense, `life=0`, and supplied noncritical Flash `random(200)` rolls of 199. The synthetic 11x11 grid includes sentinel cells to distinguish normal one-cell clearance from original boss 31/32's non-centered 3x3 footprint. The oracle checks special pre-battle HP losses for IDs 10, 12, 17, 20; exact final HP, reward money/experience, frame action counts, stage sequence, boss 19 early flag, and caller immutability.

**Scope and gate:** These are source-data-driven synthetic regression vectors, **not** recorded original Flash fights. They do not verify Flash playback, real timing, random distribution, critical probability, death behavior, plot, shops, all floor events, audio, screenshots, or ending. No asset binding or training environment is enabled. Keep `gameplay_parity_verified`, `gymnasium_ready`, and `kaggle_started` false until full automated and manual acceptance.

## Critical-roll boundary extension (2026-11-01)

The two runtimes now additionally exercise **33 monster IDs × 2 supplied Flash random(200) values = 66 synthetic critical-boundary scenarios per runtime** (132 cross-runtime executions). At `life=0`, roll `0` satisfies the existing frame-24 `roll <= life` branch and doubles hero damage, producing a one-action kill; roll `1` does not, producing two hero hits and one seven-HP counterattack. The tests also check special pre-battle damage, gold/experience rewards, cleared target, and input immutability.

This specifically protects the easily missed inclusive comparison at the critical threshold. It exercises the current source-attributed frame-24 probes, but **does not independently re-extract the frame-24 ActionScript in this increment**, establish random distribution, death behavior, actual Flash playback, or complete game parity. All training gates remain false.
