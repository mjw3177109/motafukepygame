# mt_06 isolated Pygame / Chromium smoke

Source: original `game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`, FFDec Shape 197 (`shapes/197.svg`), DefineSprite 198, and independently pinned 16px/16px registration. This is **not** a runtime floor asset binding.

The new `tools/smoke_mt06_candidate.py` first validates the FFDec manifest, Shape 197 source SHA256, RECT, registration report, and unapproved candidate state. It then decodes the original SVG through CairoSVG into a real Pygame 64×64 Surface and separately through real Chromium Canvas. Both draw at (16,16). The workflow saves `mt_06_pygame.png`, `mt_06_chromium.png`, and a JSON report with PNG hashes, alpha bounds, and RGBA differences.

The candidate remains excluded from `core/static_svg_assets.py` and `web/static_svg_assets.mjs`. Pixel differences between Pygame and Chromium are diagnostic, **not** proof of original Flash equivalence. The report explicitly keeps runtime binding, Flash visual parity, gameplay parity, Gymnasium, and Kaggle approval false.

To run after the existing FFDec extraction and Shape audit:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m tools.smoke_mt06_candidate \
  --manifest .swf_audit/manifest.json \
  --registration .swf_audit/shape_registration_report.json \
  --anchors data/original_shape_registration_anchors.json \
  --export-root .swf_audit/export \
  --out-dir .swf_audit/mt06_candidate
```

Next gate: compare both PNGs against a separately captured, provenance-checked original Flash 1.12 frame under equivalent scale and placement. Do not approve the asset until a human also verifies it. Other sprite aliases, game events, shops, ending, and end-to-end parity remain unverified.
