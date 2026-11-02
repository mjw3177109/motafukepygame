# Original FFDec static SVG raster smoke (Pygame)

The SWF audit now uses the **actual** FFDec-exported `shapes/222.svg` and
`shapes/219.svg`, with the source-hash/registration checks in
`core.static_svg_assets`, the real CairoSVG-to-Pygame decoder, and the
`core.verified_static_preview` drawing adapter. This replaces synthetic
images for this one smoke check only.

It renders each verified static alias on a transparent 64x64 Pygame Surface,
rejects empty/clipped alpha, and saves two PNGs and `report.json` into the
`original-flash-audit` Actions artifact. Each report records source SWF
SHA256, SVG SHA256, output PNG SHA256, alpha count and alpha bounds.

Run after the FFDec extraction and Shape registration audit:

```bash
python -m pip install 'pygame==2.6.1' 'CairoSVG==2.8.2'
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m tools.smoke_original_static_render \
  --manifest .swf_audit/manifest.json \
  --report .swf_audit/shape_registration_report.json \
  --anchors data/original_shape_registration_anchors.json \
  --export-root .swf_audit/export \
  --out-dir .swf_audit/static_preview
```

**Scope**: a non-empty real Pygame raster is evidence of source SVG decode and
draw, **not** evidence of matching original Flash pixels, correct animation,
full-floor display, HTML5 screenshot parity or gameplay/ending completion.
The original Flash screenshots are not yet available as reference images.
Do not open the Gymnasium/Kaggle gate on this evidence.
