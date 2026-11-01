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
