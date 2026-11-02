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

## Fractional registration isolation (2026-10-31)

The same CI command now also records a source-preserving Chromium Canvas registration experiment for each verified SVG. It keeps the original SVG and Pygame baseline unchanged, and draws the Chromium image at four independently controlled registration offsets: `pinned` (15.95, 15.95), `snap-x` (16, 15.95), `snap-y` (15.95, 16), and `snap-xy` (16, 16). The pinned render must reproduce the archived Chromium raster byte-for-byte; otherwise the audit fails. The JSON `sprites.*.registration_probe` records the actual origins, pixels changed from the pinned Chromium image, and Pygame-versus-Chromium RGBA/Alpha counts, Alpha bounding box, columns and value pairs. This isolates whether X or Y subpixel placement contributes to the 32-pixel Alpha edge stripe; it does not establish original Flash rendering behavior. Do not switch production registration to rounded coordinates without a Flash reference screenshot and event/visual review.

Four dependency-free tests cover independent axis snapping, unequal axes, integral offsets, and invalid/non-finite inputs. The existing `SWF Original Audit` command runs the expanded experiment and archives its JSON; no workflow trigger or production renderer changes are required.

## Registration RGB visibility audit (2026-10-31)

The same source-verified four-mode experiment now reports **RGB and composited visual differences**, in addition to the existing alpha stripe diagnostics, for both `pygame_vs_chromium` and `chromium_changed_from_pinned`. Each mode records raw RGBA/RGB/alpha mismatch counts, visible versus fully transparent RGB mismatches, opaque black/white backdrop comparisons, and edge/interior/outside mismatch regions. Region totals are cross-checked against raw RGBA and alpha totals; inconsistencies fail the audit.

This closes a diagnostic blind spot: snapping X may remove the 32 alpha mismatches while changing many **interior RGB pixels**. It is not valid to conclude that X snapping improves Flash fidelity merely because alpha differences become zero. The report remains an experiment, and no production registration coordinates, source SVGs, original SWF, or RL/Kaggle gate have changed. Three synthetic regression tests cover independent edge alpha and interior RGB, hidden RGB, and identical rasters. Real counts must be read from the new CI artifact, not inferred from older reports.
