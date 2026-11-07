# Encounter pipeline composition (not full 1:1 signoff)

Source: `game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`.
The four raw monster vectors in `tests/fixtures/encounter_pipeline_cases.json` are taken from the FFDec-derived `original_tables.json` (boss_man[0] and boss_man[20]). Hero values and random rolls are **synthetic test inputs**, not recordings of the original player.

`core/encounter_pipeline_probe.py` and `web/encounter_pipeline_probe.mjs` compose the existing verified probes:
`Move_arrow` encounter gate -> sprite frame1 -> frame24/34 loop -> frame35 reached -> frame54 handoff -> sprite855 / `Move_arrow(100)` settlement.
Both consume explicit critical-roll sequences and reject missing or surplus rolls. Blocked encounters must consume no rolls. The wrapper refuses non-idle `display_kill` to prevent an accidental duplicate pipeline call; this is a **harness safety precondition**, not a newly proven original keyboard gate.

Regression vectors cover blocked encounters, one-hit kill with no phantom retaliation, two-hit combat with one retaliation, and mage's 100 HP prebattle loss. They check map clearance, HP, money, experience, state immutability and action counts across both runtimes.

**Limitations:** no real Flash input capture, sprite timing, death/ending, modal events, save/load, stair/shop/plot logic, renderer or audio. Passing these tests proves composition consistency only, not original end-to-end 1:1 parity. RL/Kaggle remains gated.
