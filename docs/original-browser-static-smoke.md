# Real Chromium static SVG render smoke

After FFDec extracts the original `game.swf`, this audit renders the two source-verified static SVG aliases `mt_00` (Shape 222) and `mt_01` (Shape 219) using **real Chromium Canvas** and the existing `web/verified_static_preview.mjs` path.

The browser runs on a loopback HTTP origin (needed for Web Crypto SHA256). The server exposes only the three required JS modules and two pinned FFDec SVG paths. Both SVGs must match the original manifest and shape registration report. The actual `createImageBitmap` and `drawImage` browser code runs, not a mock decoder. The preview remains input-locked.

The audit checks PNG signature, nonempty alpha, 64x64 canvas, clipping and Chromium/Pygame alpha-bounding-box differences of at most 2 pixels per component. It records both PNG hashes and an explicit `flash_pixel_parity_verified: false`. Rasterizers can produce different pixel colors/alpha; the tolerance is **not** evidence of Flash pixel equivalence.

CI: `SWF Original Audit` exports FFDec sources, runs the Pygame smoke first, then runs the Chromium smoke with Playwright. Artifacts: `.swf_audit/browser_preview/mt_00.png`, `mt_01.png`, and `report.json`. Do not enable Gymnasium/Kaggle from this check.

Manual rerun after the FFDec audit:
```sh
python -m pip install playwright==1.56.0
python -m playwright install chromium
python -m tools.smoke_original_browser_static --manifest .swf_audit/manifest.json --report .swf_audit/shape_registration_report.json --anchors data/original_shape_registration_anchors.json --pygame .swf_audit/static_preview/report.json --export-root .swf_audit/export --out-dir .swf_audit/browser_preview
```
