# Source-verified SVG image-rendering experiment (2026-10-31)

This is a diagnostic only, not a Flash parity test. The source-hashed FFDec SVGs mt_00 (Shape 222) and mt_01 (Shape 219) are never modified on disk. The experiment verifies SWF/Shape/SVG provenance and reproduces both archived Pygame/CairoSVG and Chromium baselines exactly before comparing temporary in-memory image-rendering variants (original, auto, pixelated, crisp-edges).

Run after the static raster smoke steps:
python -m tools.experiment_svg_image_rendering --manifest .swf_audit/manifest.json --registration .swf_audit/shape_registration_report.json --anchors data/original_shape_registration_anchors.json --export-root .swf_audit/export --pygame-dir .swf_audit/static_preview --browser-dir .swf_audit/browser_preview --out .swf_audit/svg_image_rendering_experiment.json

Local reproduction from the source-hashed GitHub Actions artifact 13050649030, with local Chromium and CairoSVG 2.8.2:

| Alias | Original RGBA differences | Pixelated RGBA differences | Chromium pixels changed by pixelated | CairoSVG pixels changed | Alpha differences |
| --- | ---: | ---: | ---: | ---: | ---: |
| mt_00 | 899 | 848 | 894 | 0 | 32 |
| mt_01 | 932 | 874 | 925 | 0 | 32 |

The two embedded 32x32 PNGs use an FFDec patternTransform of matrix(1.0667, 0.0, 0.0, 1.0667, -17.05, -17.05), and the outer SVG has a 15.95px translation. Explicit auto and crisp-edges had the same mismatch counts as the original in this local experiment. Pixelated changes hundreds of Chromium colors and reduces cross-renderer differences, but does not fix the edge alpha differences. This implicates image sampling as a contributor, NOT proof of which renderer matches Flash. Do not change production renderer behavior without original Flash screenshots.

CI repeats the experiment using its own renderer versions and archives JSON. Baseline reproduction failure is a hard error. The report does not unlock gameplay, ending, 1:1, Gymnasium or Kaggle gates.
