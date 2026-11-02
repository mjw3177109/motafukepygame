# FFDec floor sprite alias coverage (not visual parity)

This audit closes the asset-readiness accounting gap after the Pygame and Canvas draw adapters. It reads the original 27 matrices in `data/original_floors.json` (from `game.swf`, SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`) and reuses `plan_jump_floor_tiles` rather than inventing sprite aliases.

The `SetLineDisplay(1)` path covers floors 01–26. Floor 00 follows a different entry path and is excluded. Flash movie clips can combine shapes, images and timelines; `mt_XX` is not necessarily an FFDec PNG filename. The report is a missing-work inventory, **not** a parity score.

Run after Java 8 FFDec extraction:

```bash
python tools/audit_floor_assets.py --floors data/original_floors.json --manifest .swf_audit/manifest.json --out .swf_audit/floor_asset_coverage.json
```

Optional manually curated bindings use schema version 1, matching `swf_sha256`, and a `bindings` object keyed by `mt_XX`. Each binding requires `export_path`, `sha256`, `registration_evidence_path`, `registration_evidence_sha256`, finite `origin_x` and `origin_y`, and a nonempty `review_note`. All file paths must exist in the FFDec inventory and the actual export bytes must match the hashes. Example usage:

```bash
python tools/audit_floor_assets.py --manifest .swf_audit/manifest.json --bindings bindings.json --export-root .swf_audit/export --out /tmp/floor_asset_coverage.json --require-complete
```

**No bindings are fabricated or automatically approved.** Even structurally complete mappings have `visual_parity_verified: false` and `gameplay_parity_verified: false`. Manual movie-clip registration review and Flash-vs-Pygame/Canvas screenshots are still required. The SWF audit workflow uploads this report with its FFDec artifact. Gymnasium/Kaggle remain blocked.
