# Original battle frame 34/35/54 source audit (not Flash playback)

Original SWF: `game.swf`, SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`.

Evidence: `ffdec_export.tar.gz` in GitHub Actions run 41330517045, artifact 13092724343, produced 2026-11-01. The archive preserves the following FFDec source files:

| Frame | Exact FFDec byte SHA256 | Source behavior |
|---|---|---|
| 34 | `68fba28365be1e2a113611697ec24e3d96da3e9c3b08b3f6d96644744440972e` | If `left_hp > 0`, jump to frame 24 |
| 35 | `6e9dbc778499938292edc758151c4a5095cd0d1ac5361b0d2ebbe057d17b121c` | Play `music_07` |
| 54 | `112c9ad7454ad425124e1ccb6481ed71ddba58ad36ebc5dba6639a07f367893c` | `stop()`; `Display_kill=2`; `Now_hp=right_hp` |

The three fixtures retain exact FFDec CRLF bytes (44, 30, 60 bytes). The audit checks original SWF identity, exact byte hashes, normalized fingerprints and source clauses. CI independently re-reads fresh FFDec exports rather than trusting committed fixtures; missing or changed scripts fail closed. The report explicitly marks playback, death handling, full battle, overall parity, Gymnasium and Kaggle as **unverified**.

Run after FFDec extraction:

```bash
python -m tools.audit_original_battle_transitions --export-root .swf_audit/export --swf game.swf --out .swf_audit/original_battle_transitions_audit.json
```

**Limitation:** Frame 34 fall-through to frame 35 is inferred from the sprite timeline, not independently proven by Flash playback. Frame 54 preserves `right_hp` (possibly negative), but death/ending branches are not yet verified. Existing Python/JavaScript deterministic probes do not establish true Flash gameplay parity. Next: obtain independent Flash victory and death traces, compare both runtimes and address mismatches. RL/Kaggle remain blocked.
