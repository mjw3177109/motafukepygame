# mt_06 saved-render artifact verification

The independent `tools/verify_mt06_artifacts.py` gate reopens the **archived**
`mt_06_pygame.png` and `mt_06_chromium.png` after the renderer writes them.
It checks PNG SHA256 values, exact 64×64 RGBA format, alpha metrics, and
recomputes every pixel-difference field. It also matches the reported SWF and
Shape 197 SVG hashes to `data/original_shape_registration_anchors.json` and
rejects any attempt to mark visual/gameplay parity, runtime binding, Gymnasium,
or Kaggle as approved.

This closes the gap where a successful render process could archive stale,
substituted, or corrupted PNGs alongside an apparently valid in-memory JSON
report. It is **not** an independent Flash-player screenshot or gameplay test.

After `tools.smoke_mt06_candidate` finishes, run:

```bash
python -m tools.verify_mt06_artifacts \
  --report .swf_audit/mt06_candidate/report.json \
  --png-dir .swf_audit/mt06_candidate \
  --anchors data/original_shape_registration_anchors.json \
  --out .swf_audit/mt06_candidate/artifact_verification.json
```

Fail closed on any mismatch; do not approve the sprite or start RL training.
Next: capture and provenance-check a separate original Flash frame and compare
it to both saved renderers under equivalent placement and scale, with human QC.
