# Original SWF sprite placement timeline audit — all 84 aliases

Source: game.swf SHA256 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9 and the Java 8 / FFDec -dumpSWF tag dump. The source and tag-dump hashes are checked against the symbol trace, frame report and 84 per-alias timeline anchors.

The parser decodes PlaceObject2 (including Move updates), RemoveObject2, SWF MATRIX 16.16 coefficients, integer twip translations, clip depth, ShowFrame boundaries, DoAction offsets (recorded, never executed), SoundStreamHead2 (ignored for display-list state), and null-terminated FrameLabel strings. It now covers every alias in the source-linked ExportAssets trace instead of a fixed five-sprite sample.

Verified on the current original artifact:
- 84/84 traced sprite aliases have decoded placement timelines.
- 1,997 frame display-list snapshots were reconstructed.
- The five original timeline anchors (mt_00, mt_01, mt_02, mt_03, mt_06) remain unchanged; 79 additional source timeline hashes were pinned.
- mt_99 FrameLabel tags were attached to frames 1, 18, 37 and 56: one, three, five, sever.
- 9 DoAction tag offsets remain uninterpreted across mt_02, mt_03, mt_04, mt_05, mt_15 and mt_99.

FrameLabel is decoded only in the simple null-terminated form present in this SWF. Unexpected trailing/anchor bytes, unknown nested tags, malformed MATRIX fields, depth lifecycle errors, missing frames, source drift, incomplete symbol coverage or incomplete anchor coverage fail closed.

This is a structural display-list snapshot, NOT sprite rendering or game execution. It does not prove nested-sprite compositing, masks, color transforms, SVG/bitmap registration, audio, frame-rate timing, Flash screenshot parity, floor binding, ActionScript behavior or gameplay parity. Do not claim 84/84 visually bound.

Run after the symbol and frame audits:

    python -m tools.audit_sprite_placements --tags .swf_audit/ffdec_tags.log --trace .swf_audit/swf_symbol_trace.json --frames .swf_audit/swf_sprite_frames.json --anchors data/original_sprite_placement_anchors.json --out .swf_audit/swf_sprite_placements.json

The expanded review queue is expected to contain 29 one-frame identity-placement candidates for independent Flash screenshot review and 55 multi-frame timelines still requiring timeline composition/rendering. Structural floor binding remains separate. Gymnasium/Kaggle remains blocked.
