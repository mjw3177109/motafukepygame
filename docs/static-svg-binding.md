# Audited static SVG loader for Pygame and HTML5

Use the FFDec audit outputs: shape_registration_report.json, manifest.json,
data/original_shape_registration_anchors.json, and export/shapes/*.svg.
The two loaders check SWF SHA linkage, original Shape IDs, SVG SHA256 bytes,
and verified registration offsets before decoding any image.

Python: core.static_svg_assets.load_verified_static_assets(report, anchors,
manifest, export_root). The default decoder requires CairoSVG and Pygame;
unit tests inject a fake decoder. HTML5: web/static_svg_assets.mjs exports
loadVerifiedStaticAssets({report,anchors,manifest,readSvg,decodeSvg}).
The default browser reader fetches paths relative to the page; a caller
must point it to the actual FFDec export directory.

Only mt_00 and mt_01 are supported. The returned mapping is compatible
with floor_render, but a full floor is still blocked until every other
required alias is verified. No pixel parity, Flash raster equivalence,
animation, gameplay, ending, or Gymnasium/Kaggle training is claimed.
