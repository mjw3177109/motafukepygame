# Source-linked asset review queue (2026-11-01)

This tool joins four freshly generated source-hashed reports: floor alias coverage, ExportAssets/DefineSprite/Shape trace, declared/observed sprite frames, and decoded PlaceObject2 timelines. It rejects mismatched SWF/tag hashes, missing aliases, inconsistent frame counts, invalid shape hashes, and malformed placement evidence.

Run after original symbol, frame and placement audits:

    python -m tools.build_asset_review_queue --coverage .swf_audit/floor_asset_coverage.json --trace .swf_audit/swf_symbol_trace.json --frames .swf_audit/swf_sprite_frames.json --placements .swf_audit/swf_sprite_placements.json --out .swf_audit/asset_review_queue.json

Stages: static_screenshot_review requires one hashed shape, one frame, and an independently decoded identity placement without clipping or uninterpreted DoAction; decode_static_placements requires more timeline decoding; decode_animated_timeline requires multi-frame decoding and rendering. All stages are manual work queues, NOT proof that original Flash pixels, animation or events are reproduced. The binding_structurally_mapped flag reflects only the existing structural coverage report and never sets visual parity true.

On the 2026-11-01 original-flash-audit artifact from run 41256077869, the tool yielded 84 source-linked aliases: 2 static screenshot review candidates (mt_00, mt_01), 27 pending static placement decoding, and 55 pending animated timeline decoding. The 2 are candidates for independent Flash screenshot comparison, NOT visually verified sprites. No original resources are modified and Gymnasium/Kaggle remain blocked.
