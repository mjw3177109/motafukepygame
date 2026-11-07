# FFDec source SVG sampling inventory

The Pygame/CairoSVG versus Chromium/Canvas comparison still differs at hundreds of RGBA pixels in mt_00 and mt_01. The alpha differences are confined to a left-edge column, while most RGB differences are inside the sprites. These are observations, not proof of a registration or filtering root cause.

This new source-bound diagnostic reads only the two FFDec-exported original SVGs. It verifies each SVG SHA256 against both the FFDec manifest and the independently audited Shape registration report, then records SVG pattern geometry/transforms and image references. For embedded PNG data URIs, it records the decoded payload hash and IHDR dimensions, color type, bit depth and interlace mode; PNG IHDR CRC is validated. Image-rendering hints are preserved verbatim, not interpreted as a promise about Chromium or CairoSVG behavior. External image URLs are never fetched.

Run after audit_shape_registration:

    python -m tools.audit_svg_sampling --manifest .swf_audit/manifest.json --registration .swf_audit/shape_registration_report.json --export-root .swf_audit/export --out .swf_audit/svg_sampling_report.json

The original SWF audit CI uploads the JSON report with other evidence. A report with no patterns or images is a valid finding, not an excuse to invent an embedded bitmap. The diagnostic does not change renderer output or assert Flash parity. Next: inspect the real report and design a controlled nearest-neighbor versus interpolated raster experiment, using source-hashed originals and separate edge/interior measurements.

Gymnasium and Kaggle remain blocked until the game, original events, map, ending and both renderers pass the required independent verification.
