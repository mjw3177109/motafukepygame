# Original Flash raw monster/base-stat provenance audit

This is **source data verification, not combat or gameplay parity**. The original
game.swf was exported using the repository's FFDec/Java 8 workflow. The
successful original-flash-audit artifact from the 2026-11-01 run contained
original_tables.json and a 911-file FFDec archive. The raw
export/scripts/frame_4346/DoAction.as in that archive was independently
SHA256-checked against the extracted table source
(2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c).

data/original_combat_tables.json pins **33 monster arrays (IDs 0..32, five
integer fields plus original text) and nine starting stat integers**. The field
order is preserved as raw ActionScript array order. **No field meaning, battle
formula, event effect, or complete playable result has been inferred.**

The CI verification requires all three independent inputs: committed raw
values, freshly extracted FFDec original_tables.json, and the existing
data/original_floors.json source SHA anchors. It also re-hashes the original `game.swf` bytes (rather than trusting only
three matching JSON SHA fields) and the exported ActionScript bytes. Any value/name/stat/ID, source, field-order, or safety-gate
drift fails the audit; success writes original_combat_tables_audit.json and
keeps combat/gameplay, Gymnasium, and Kaggle gates false.

Run after FFDec extraction:

    python -m tools.verify_original_combat_tables --committed data/original_combat_tables.json --extracted .swf_audit/original_tables.json --floor-anchors data/original_floors.json --export-root .swf_audit --swf game.swf --out .swf_audit/original_combat_tables_audit.json

Next: derive combat field semantics and formulas independently from original
ActionScript control flow, then compare Flash traces to Pygame and HTML5.

## 2026-11-01: independent raw-source reparse gate

The audit now reparses the **actual hashed FFDec ActionScript bytes** using the
same strict monster/base declaration grammar as the original extractor. It
compares all 33 six-field arrays and nine starting stats against that source,
not merely two JSON copies that can be edited together. Duplicate or missing
source declarations fail closed. Three synthetic regression cases cover
colluding JSON edits to a monster, colluding edits to HP, and a valid-hash
script with incomplete declarations. This verifies provenance only: monster
field meanings, damage formulas, gameplay and Flash parity remain unapproved.
