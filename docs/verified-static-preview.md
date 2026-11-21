# Original static SVG preview handoff (Pygame and HTML5)

`core.verified_static_preview.render_verified_static_preview` and
`web/verified_static_preview.mjs:renderVerifiedStaticPreview` connect the
existing SHA256-verified `mt_00`/`mt_01` loaders to the existing depth-ordered
floor renderers. Both use the same source-derived registration offsets.

These entry points are **static-only diagnostic previews**, not full-floor
renderers. They refuse animated or unverified aliases, an unlocked floor, and
empty plans. The loader checks both SVG hashes before decoding either image;
the renderer checks all placements before drawing anything. They do not
clear the canvas, advance Flash animation, unlock input, update floor state,
or assert visual parity. They also cannot substitute for an original Flash
screenshot comparison.

Python usage (CairoSVG/Pygame needed for the default decoder):

```python
from core.verified_static_preview import render_verified_static_preview
count = render_verified_static_preview(surface, plan, report, anchors,
    manifest, ffdec_export_root)
```

HTML5 usage (readSvg must point to the verified FFDec export directory):

```js
import {renderVerifiedStaticPreview} from './verified_static_preview.mjs';
const count = await renderVerifiedStaticPreview(ctx, plan, {
  report, anchors, manifest, readSvg, decodeSvg
});
```

The tests use **synthetic, hashed SVGs** to verify the actual handoff and
failure-before-draw semantics. Real FFDec SVG rasterization, original Flash
pixel comparison, animation and gameplay remain unverified. No Kaggle training.
