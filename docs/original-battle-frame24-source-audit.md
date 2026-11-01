# Original mt_other_04 frame-24 source audit (not Flash gameplay parity)

Source: game.swf, SHA256 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9.
FFDec export: export/scripts/DefineSprite_453_mt_other_04/frame_24/DoAction.as, SHA256 98e293ed7fbfd1c0a6340c53a973fabf0a4c26f235467be6b1f3398469d24196.
Both hashes were independently measured from GitHub Actions run 41325213475, artifact 13091021680, on 2026-11-01.

This increment independently pins the original frame-24 script and verifies its critical-roll and alternating-turn clauses. Flash random(200) returns 0..199; the source uses kill_max <= _root.Now_life (inclusive), doubles hero damage on critical, clamps monster HP to zero, does not clamp hero HP on retaliation, increments kill_number, and jumps to frame 35 from the monster turn when left_hp == 0. Exact byte and normalized-source hashes reject unreviewed source changes. The 728-byte test fixture preserves the FFDec-exported CRLF bytes.

CI runs the audit after FFDec extraction against newly exported ActionScript and original SWF bytes. This static source check does not prove Flash playback, random distribution, timing, death behavior, frame-34/35/54 transitions, rewards, graphics, maps, story, ending, or full Pygame/HTML5 parity. Existing synthetic critical tests are not Flash recordings. RL/Gymnasium/Kaggle remain blocked.

After SWF extraction, reproduce using:

    python -m tools.audit_original_battle_frame24 --script .swf_audit/export/scripts/DefineSprite_453_mt_other_04/frame_24/DoAction.as --swf game.swf --out .swf_audit/original_battle_frame24_audit.json

Next: independently pin frame-34/35/54 transitions and compare recorded original Flash battle/death traces to both runtimes.
