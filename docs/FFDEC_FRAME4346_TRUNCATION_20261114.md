# FFDec frame_4346 non-deterministic export: verified evidence (2026-11-14)

## Provenance
- Source: GitHub Actions SWF Original Audit run [43641728710](https://github.com/mjw3177109/motafukepygame/actions/runs/43641728710), commit `c9801255d8b8381616a5710fa4f88436c9f65f41`.
- Failure artifact: `original-flash-audit`, artifact ID `14132601774` (retained until 2026-11-28); downloaded and inspected as ZIP.
- Original `game.swf` SHA-256 from run log: `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`.
- Both FFDec export invocations returned 0 and each inventory contained 911 files; one path differed: `scripts/frame_4346/DoAction.as`. Eight casefold collision groups remain separate and are not the cause of this mismatch.

## Byte-level evidence
| Export | Size (bytes) | Lines | SHA-256 |
| --- | ---: | ---: | --- |
| `.swf_audit/export/scripts/frame_4346/DoAction.as` | 20710 | 421 | `2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c` |
| `.swf_audit_repeat/export/scripts/frame_4346/DoAction.as` | 10314 | 200 | `66a30ed811ca2932119053f303c6903fd15323efae90824441f6fcefe1baa7e7` |

The shorter second export agrees through `mt_line_16[3]`, then ends with the malformed-looking sequence:

```actionscript
mt_line_16;
4;
new Array(20,20,20,1,26,119,1,1,20,20,20);
```

The first export instead continues with `mt_line_16[4] = new Array(...)`, remaining floor arrays, and further code. The differing output is **not evidence that the original SWF changes**; it is evidence that the FFDec decompiled-text export is not deterministic in this run. The shorter output cannot be accepted as a complete floor-table source. Do not normalize away this difference, silently choose either export, or mark source parity as passing.

## Reproduction and acceptance gate
1. Retrieve the artifact while retained, compare both files byte-for-byte and review the unified diff near `mt_line_16[4]`.
2. Re-run independent FFDec exports using the pinned repository JAR and Java 8, record invocation logs and manifest hashes; preserve the failure when mismatched.
3. Inspect the raw SWF ActionRecord / bytecode for the affected frame to distinguish decompiler truncation from other issues. Do not infer bytecode semantics solely from the malformed decompiled output.
4. Only after source extraction is stable, resume the downstream floor/combat audit and independent Pygame/HTML5 runtime comparisons.

**Status:** diagnostic evidence only; root cause not established, no gameplay parity or RL/Kaggle gate approved.
