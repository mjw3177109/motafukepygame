# Original Flash combat field semantics: source audit (not game parity)

Original game.swf SHA256: 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9.
FFDec renderer ActionScript: export/scripts/frame_4346/DoAction_2.as, SHA256
0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034.
Hashes are checked against data/original_floors.json and original SWF bytes.

The renderer's mt_kills assignments establish boss_man indices 0/1/2 as monster
HP/attack/defense. Move_arrow(100) reward assignments establish indices 3/4 as
gold/experience. Index 5 is the original name string in the separate DoAction.as
declaration audit. These are static source semantics, not live gameplay parity.

The source audit also checks the original encounter estimate
int(HP / (hero attack - monster defense)) * (monster attack - hero defense),
the monster defense >= hero attack and estimated loss > hero HP denial gates,
and four entry-estimate bonuses: monster ID 20 +100, 12 +300,
10 int(hero HP / 4), 17 int(hero HP / 3).

The special damage applied after acceptance and the actual sprite battle loop
remain separate. Never conflate the entry estimate with final HP loss.
Flash frame timing, random criticals, death, rewards, UI, story, ending,
and Pygame/HTML5 full parity are not established. Gymnasium/Kaggle stay blocked.

After FFDec extraction:
python -m tools.audit_combat_field_semantics --script .swf_audit/export/scripts/frame_4346/DoAction_2.as --swf game.swf --floors data/original_floors.json --combat data/original_combat_tables.json --out .swf_audit/original_combat_semantics_audit.json

Synthetic regression tests deliberately re-hash tampered scripts to prove that
field-index, formula and special-bonus checks go beyond matching hashes.
