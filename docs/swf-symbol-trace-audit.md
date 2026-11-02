# SWF ExportAssets → DefineSprite → Shape provenance (2026-10-30)

Evidence: `game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`, Java 8 FFDec `-dumpSWF` (`ffdec_tags.log`), and the hashed FFDec `manifest.json` / `floor_asset_coverage.json`. The `SWF Original Audit` workflow regenerates all three inputs and verifies every referenced SVG's bytes.

**Verified symbol linkage, not verified pixels:** all 84 required `SetLineDisplay(1)` floor aliases (floors 01–26) resolve through `ExportAssets` to a `DefineSprite`, whose `PlaceObject2` entries reference 152 unique `DefineShape` IDs with hashed SVG exports. Repeated exports with the **same** character ID are accepted; contradictory IDs, missing definitions, missing SVGs, altered bytes, and anchor drift fail closed. The five committed anchors are `mt_00`, `mt_01`, `mt_02`, `mt_03`, and `mt_99`; they record character IDs and direct shape IDs only, not registration points.

Run after `extract_swf.py` and `audit_floor_assets.py`:

```bash
python tools/trace_swf_symbols.py \
  --tags .swf_audit/ffdec_tags.log \
  --manifest .swf_audit/manifest.json \
  --coverage .swf_audit/floor_asset_coverage.json \
  --export-root .swf_audit/export \
  --anchors data/original_sprite_symbol_anchors.json \
  --out .swf_audit/swf_symbol_trace.json
```

The generated `swf_symbol_trace.json` is an Actions artifact, not a manually approved asset binding. The FFDec SVGs may contain embedded bitmap patterns, and a sprite can have multiple frames and shapes. This audit does **not** reconstruct SWF transforms, frame timings, compositing, registration offsets, interactions, or pixel parity. Therefore the existing `audit_floor_assets.py` count remains **0/84 verified visual bindings** until human-reviewed registration evidence and original-vs-client screenshots exist. Floor 00 is outside this path. Gymnasium/Kaggle remain blocked.
