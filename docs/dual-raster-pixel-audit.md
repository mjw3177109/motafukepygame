# Pygame / Chromium original-SVG pixel delta audit

Scope: source-hashed FFDec mt_00 (Shape 222) and mt_01 (Shape 219) only. The new tools/audit_dual_raster_pixels.py checks both PNG SHA256 values, original SWF/Shape provenance, raster dimensions, alpha counts and bounding boxes before comparing pixels. It records RGBA/RGB/alpha mismatch counts, maximum and mean channel deltas, and the changed-pixel rectangle. A nonzero pixel difference is a diagnostic, not a failed Flash-parity gate; invalid evidence is a hard failure.

Run after both existing original-SVG smoke tests:

    python -m tools.audit_dual_raster_pixels --pygame-dir .swf_audit/static_preview --browser-dir .swf_audit/browser_preview --registration .swf_audit/shape_registration_report.json --anchors data/original_shape_registration_anchors.json --out .swf_audit/dual_raster_pixel_report.json

Initial investigation of the verified 2026-10-31 source-hashed PNGs from commit 4052ccf3bd8f68fc46848b037ded3a288b3edd01:

| Alias | Different RGBA pixels | Different RGB pixels | Different alpha pixels | Max absolute RGBA delta |
| --- | ---: | ---: | ---: | --- |
| mt_00 | 899/4096 | 897 | 32 | [18,18,18,12] |
| mt_01 | 932/4096 | 931 | 32 | [25,25,25,12] |

Both have identical 32x32 alpha bounds at (16,16) and 1024 visible pixels, but 32 edge pixels differ in alpha. This is consistent with rasterizer/sampling differences, not proof of their cause; investigate embedded SVG pattern sampling, transforms and edge antialiasing using original export files before changing production rendering.

This comparison is NOT against the Flash player and does not establish 1:1 visual, event, game or ending parity. It does not unlock Gymnasium/Kaggle. Pixel values can change across browser/CairoSVG versions, so the script records rather than pins mismatch counts. Retain the source PNGs and the new JSON report as CI artifacts for reproducible analysis.

## Alpha-edge localization (2026-10-31)

A second inspection of the two archived 64x64 source PNG pairs localized **all 32 alpha mismatches per sprite** to the single left-edge column `x=16`, spanning `y=16..47`. In each pair, Pygame alpha is `255` and Chromium alpha is `243` on those 32 pixels; other columns have matching alpha. The audit now records `alpha_difference_bounds_xywh`, per-column counts and alpha-value-pair histograms, so future CI can expose changes without hardcoding a renderer-specific pixel count as a success criterion.

The observed 243/255 coverage (~95.3%) is consistent with fractional SVG edge coverage near the separately measured 15.95px registration offset. **This is a hypothesis, not an established cause or a Flash reference.** Do not force alpha to 255, shift the sprite, or mark parity as passed without comparing original Flash output and source SVG path/pattern geometry.

## Independent provenance binding (2026-10-31)

The two renderer reports previously only checked that their claimed Shape IDs and SVG hashes agreed with each other. Two equally incorrect reports could pass that check. The audit now requires the separately FFDec-verified `shape_registration_report.json` and the committed SWF registration anchors; both renderer reports must match the pinned Shape ID, source SVG SHA256, SWF SHA256, and registration coordinates. Jointly forged IDs/hashes and drifted anchor/report data are regression-tested. This closes a source-evidence gate only; it does **not** prove the alpha-edge hypothesis, Flash pixel equivalence, gameplay parity, or completion.


## Visibility-aware comparison (2026-10-31)

The original RGBA mismatch count is a byte-level diagnostic, not a count of
visually different pixels. RGB values can differ while both alpha channels are
zero; those bytes are invisible after ordinary alpha compositing. The audit now
separately reports visible-vs-fully-transparent RGB mismatches and 8-bit
straight-alpha composited RGB mismatch counts over opaque black and white
backgrounds. Each channel is rounded with
`(rgb * alpha + background * (255 - alpha) + 127) // 255`.
The existing raw RGBA counts are retained unchanged for regression continuity.

A black sprite edge can have different alpha yet look identical on black and
different on white; this is regression-tested. These backdrop probes are
diagnostic only. They neither establish the root cause of the 15.95px edge
sampling nor substitute for original Flash screenshots or gameplay parity.


## Edge versus interior attribution (2026-10-31)

The dual-raster audit now records `difference_regions` for every verified PNG
pair. It classifies mismatched RGBA and alpha pixels as `edge`, `interior`
or `outside` using four-neighbour alpha visibility (>1), conservatively
treating a pixel visible in only one renderer as edge. This is a **spatial
diagnostic**, not a causal test or an original Flash reference.

Reanalysis of the archived source-hashed PNG pairs from commit
`4052ccf3bd8f68fc46848b037ded3a288b3edd01` produced:

| Alias | RGBA edge | RGBA interior | RGBA outside | Alpha edge | Alpha interior |
| --- | ---: | ---: | ---: | ---: | ---: |
| mt_00 | 120 | 779 | 0 | 32 | 0 |
| mt_01 | 115 | 817 | 0 | 32 | 0 |

The majority of RGBA differences are **inside** the visible sprite, although
all alpha differences are on the edge. Therefore the left-edge 15.95px
registration hypothesis cannot, on its own, explain the interior RGB
differences. Next investigate the embedded SVG bitmap pattern's color
sampling/interpolation separately from boundary alpha coverage. Do not
normalize RGB or shift production assets based on this diagnostic alone.
The new independent six-case synthetic test suite runs in normal Python CI.
