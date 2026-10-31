# Pygame / Chromium original-SVG pixel delta audit

Scope: source-hashed FFDec mt_00 (Shape 222) and mt_01 (Shape 219) only. The new tools/audit_dual_raster_pixels.py checks both PNG SHA256 values, original SWF/Shape provenance, raster dimensions, alpha counts and bounding boxes before comparing pixels. It records RGBA/RGB/alpha mismatch counts, maximum and mean channel deltas, and the changed-pixel rectangle. A nonzero pixel difference is a diagnostic, not a failed Flash-parity gate; invalid evidence is a hard failure.

Run after both existing original-SVG smoke tests:

    python -m tools.audit_dual_raster_pixels --pygame-dir .swf_audit/static_preview --browser-dir .swf_audit/browser_preview --out .swf_audit/dual_raster_pixel_report.json

Initial investigation of the verified 2026-10-31 source-hashed PNGs from commit 4052ccf3bd8f68fc46848b037ded3a288b3edd01:

| Alias | Different RGBA pixels | Different RGB pixels | Different alpha pixels | Max absolute RGBA delta |
| --- | ---: | ---: | ---: | --- |
| mt_00 | 899/4096 | 897 | 32 | [18,18,18,12] |
| mt_01 | 932/4096 | 931 | 32 | [25,25,25,12] |

Both have identical 32x32 alpha bounds at (16,16) and 1024 visible pixels, but 32 edge pixels differ in alpha. This is consistent with rasterizer/sampling differences, not proof of their cause; investigate embedded SVG pattern sampling, transforms and edge antialiasing using original export files before changing production rendering.

This comparison is NOT against the Flash player and does not establish 1:1 visual, event, game or ending parity. It does not unlock Gymnasium/Kaggle. Pixel values can change across browser/CairoSVG versions, so the script records rather than pins mismatch counts. Retain the source PNGs and the new JSON report as CI artifacts for reproducible analysis.
