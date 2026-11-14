# SWF DefineShape RECT → FFDec SVG registration audit

Source: original game.swf SHA256 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9; Java 8 FFDec tag dump and hashed SVG exports. The auditor reads the original DefineShape RECT bitfields, checks each exported SVG width/height and SHA256, then verifies that mt_00, mt_01 and mt_06 are single-frame, single-Shape identity-matrix sprites without masks or uninterpreted actions. mt_06 is kept in a separate registration-candidate field so the existing two-sprite runtime renderer cannot silently treat it as approved.

| Shape | Original RECT (twips: xmin,xmax,ymin,ymax) |
|---|---|
| 197 | -320,320,-320,320 |
| 199 | -320,320,-320,320 |
| 211 | -159,160,-320,320 |
| 212 | -161,160,-320,320 |
| 215 | -159,159,-320,320 |
| 216 | -161,161,-320,320 |
| 219 | -319,321,-319,321 |
| 222 | -319,321,-319,321 |

Verified static SVG registration: mt_00 → Shape 222 and mt_01 → Shape 219, both origin_x=15.95px, origin_y=15.95px relative to the exported SVG top-left. Independently pinned **candidate**: mt_06 → Shape 197, origin_x=16px, origin_y=16px, original SVG SHA256 `15e5960bf4064c15af2b7086b91e437c55ccbead25425ae40149fbda20a93a70`, DefineShape offset `0001b0bd`. Candidate evidence comes from the successful 2026-11-01 original-flash-audit artifact (run 41264529808), not a Flash screenshot. These offsets are derived from original SWF bounds and identity placement, not guessed from a tile size.

Run in the FFDec audit directory:

    python -m tools.audit_shape_registration --tags .swf_audit/ffdec_tags.log --manifest .swf_audit/manifest.json --trace .swf_audit/swf_symbol_trace.json --placements .swf_audit/swf_sprite_placements.json --export-root .swf_audit/export --anchors data/original_shape_registration_anchors.json --out .swf_audit/shape_registration_report.json

This verifies source registration metadata for **2 runtime-eligible static aliases plus 1 isolated mt_06 candidate**, not runtime image binding or visual pixel parity. `verified_static_aliases` intentionally remains exactly mt_00/mt_01; `static_registration_candidates` contains mt_06 and keeps Flash visual parity false. Shape 199/211/212/215/216 bounds are source-verified, but animated mt_02/mt_03 clip/mask transforms and DoAction are not implemented. The report remains an Actions artifact, not an invented 1:1 game screenshot. Pygame/HTML5 image decoding and side-by-side Flash visual acceptance remain pending; RL/Kaggle is blocked.
