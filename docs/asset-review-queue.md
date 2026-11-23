# Source-linked asset review queue (updated 2026-11-04)

This tool joins four freshly generated source-hashed reports: floor alias coverage, ExportAssets/DefineSprite/Shape trace, declared/observed sprite frames, and decoded PlaceObject2 timelines. It rejects mismatched SWF/tag hashes, missing aliases, inconsistent frame counts, invalid shape hashes, and malformed placement evidence.

The placement audit now snapshots all 84 traced aliases (1,997 frames), including the four simple FrameLabel tags on mt_99. This advances the review queue without granting any visual approval.

Run after original symbol, frame and placement audits:

    python -m tools.build_asset_review_queue --coverage .swf_audit/floor_asset_coverage.json --trace .swf_audit/swf_symbol_trace.json --frames .swf_audit/swf_sprite_frames.json --placements .swf_audit/swf_sprite_placements.json --out .swf_audit/asset_review_queue.json

Current source-derived stages:
- 29 static screenshot review candidates: one frame, one hashed shape, one decoded identity placement, no clipping and no uninterpreted DoAction.
- 0 pending single-frame placement decodes: all single-frame aliases now have placement snapshots.
- 55 animated timelines still require further timeline composition/rendering work.

The 29 candidates are only eligible for independent Flash screenshot comparison. The existing floor asset coverage report still maps 0/84 aliases to approved runtime bindings, and none of the candidates is visually verified. The queue never sets visual or gameplay parity true. Gymnasium/Kaggle remain blocked.
