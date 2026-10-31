# Original mt_00–mt_03 placement timeline audit

Source: game.swf SHA256 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9, Java 8 + FFDec -dumpSWF output, and the existing symbol/frame reports. First exercised against the successful 2026-10-31 PR audit artifact, not guessed drawings.

This audit decodes original PlaceObject2 bytes and SWF MATRIX bit fields, preserving 16.16 fixed-point affine coefficients and integer twip translations. It reconstructs depth-indexed display lists on ShowFrame, including Move updates and clip depth. It records but does not execute DoAction. Truncated/unsupported fields, invalid depth lifecycle, mismatched labels and source hashes fail closed. Four independent timeline SHA256 anchors protect against source drift.

| Alias | Character ID | Frames | First-frame display list | Uninterpreted DoAction |
|---|---:|---:|---|---:|
| mt_00 | 223 | 1 | depth 1: Shape 222 | 0 |
| mt_01 | 220 | 1 | depth 1: Shape 219 | 0 |
| mt_02 | 217 | 10 | depths 1/2/3: Shapes 199/216/215; depth 1 clips through 4 | 1 |
| mt_03 | 213 | 10 | depths 1/2/3: Shapes 199/212/211; depth 1 clips through 4 | 1 |

mt_02 depth 3 translates from 160 to 196 twips between frames 1 and 2. mt_03 depth 2 scale X changes from 65536 to 65559 fixed16.16 between frames 1 and 2. These are source transforms, NOT rendered-pixel results.

Run after the symbol and frame audits:

    python -m tools.audit_sprite_placements --tags .swf_audit/ffdec_tags.log --trace .swf_audit/swf_symbol_trace.json --frames .swf_audit/swf_sprite_frames.json --anchors data/original_sprite_placement_anchors.json --out .swf_audit/swf_sprite_placements.json

The report contains 22 source frame snapshots. Shape/SVG registration, nested sprites, mask rasterization, color transforms, audio, ActionScript behavior, playback timing, Pygame/HTML5 screenshot parity, and ending parity remain unverified. Do not claim 4/84 visually bound. Expand only after implementing and validating additional tag variants. Gymnasium/Kaggle remains blocked.
