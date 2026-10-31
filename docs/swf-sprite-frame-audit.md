# Original SWF sprite timeline frame-count audit

Evidence: `game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`, FFDec Java 8 `-dumpSWF` (`ffdec_tags.log`), and the verified `swf_symbol_trace.json` produced by the existing workflow. The new audit checks the first four raw bytes of every relevant `DefineSprite` (character ID and declared frame count), then counts its direct nested `ShowFrame` tags. The original tag dump SHA256, sprite ID, definition offset, and five fixed original anchors must match.

**Observed in the 2026-10-31 source artifact:** 84/84 mapped sprites have matching declared and observed frame counts. Distribution: 29 one-frame, 4 ten-frame, 47 thirty-eight-frame, 1 thirty-seven-frame, 1 five-frame, 1 twenty-six-frame, and 1 seventy-four-frame sprite. In particular, `mt_00` and `mt_01` are single-frame; `mt_02` and `mt_03` each have 10 frames; `mt_99` has 74 frames. This is a source timeline count only: no evidence yet establishes per-frame transform matrices, nested timeline compositing, registration points, actual frame rate in client playback, or screenshot parity.

Run after `trace_swf_symbols.py`:

```bash
python tools/audit_swf_sprite_frames.py \
  --tags .swf_audit/ffdec_tags.log \
  --trace .swf_audit/swf_symbol_trace.json \
  --anchors data/original_sprite_frame_anchors.json \
  --out .swf_audit/swf_sprite_frames.json
```

The generated report is an Actions artifact, not a gameplay or pixel-parity certificate. Missing, extra, malformed or conflicting frame evidence fails closed. The original asset binding audit remains 0/84 visually verified; Gymnasium and Kaggle remain blocked.
