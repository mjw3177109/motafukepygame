# SWF repeat-export drift evidence — 2026-11-16 UTC

## Provenance

- Branch at inspection: `feature/mota112-swf-audit-foundation`, commit `b7a5ccd59bc97a5774e26b79971fd4cdd27de877`.
- SWF Audit run: https://github.com/mjw3177109/motafukepygame/actions/runs/43815020437 (failed).
- Diagnostic artifact: https://github.com/mjw3177109/motafukepygame/actions/runs/43815020437/artifacts/14201803429 (28 uploaded files).
- Python tooling tests on the same commit: https://github.com/mjw3177109/motafukepygame/actions/runs/43815020458 (passed).
- Source SHA-256 logged by the repeat comparator: `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`.

## Observed discrepancy (strict gate correctly failed)

Two independent FFDec exports each produced **911 files**, with identical path sets but differing ActionScript text for:

| Relative path under `scripts/` | First size | Second size | First SHA-256 | Second SHA-256 |
| --- | ---: | ---: | --- | --- |
| `frame_4346/DoAction.as` | 8630 | 20710 | `e738b31449fe3fc542b83eefeaee1357ce81dcd3ce014507406f12f25d3f6070` | `2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c` |
| `frame_4346/DoAction_2.as` | 46192 | 7618 | `0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034` | `0e5fdd156f328b3e61d29acf90090a968b95202a82c0d15b82da0d8e76803639` |

The comparator also reported eight case-folding filename collision pairs in each export. These are a portability risk, not evidence of a gameplay discrepancy.

## Next reproducible investigation

1. Download the linked artifact before its 14-day retention expires; compare both versions of each affected script byte-for-byte, retaining the exact file names and hashes.
2. Inspect the SWF's raw ActionRecords / tag boundaries for frame 4346 independently of decompiled ActionScript text. Determine whether the two exports are differently grouped or genuinely semantically different.
3. Re-run the same FFDec version with a controlled Java 8 environment and log tool version, locale, options, and file hashes. Do **not** normalize away these differences or mark the audit passed.
4. If the failure reproduces, add a narrow regression test using the captured paired outputs, with a source trace. Keep original SWF, FFDec, and strict audit unchanged.

## Scope / gates

The passing Python/JavaScript tooling CI does not establish original Flash runtime parity. Pygame and HTML5 shop UI integration, dynamic events, battle, save/load, ending, and manual original-game comparison remain unverified. Gymnasium/Kaggle training must remain blocked.
