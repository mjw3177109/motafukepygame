# FFDec ActionScript export drift diagnosis (2026-10-31)

PR #1 run 41237985460 attempt 1 failed on the anchored hash for export/scripts/frame_4346/DoAction_2.as. Attempt 2 passed. This proves differing observed outcomes, not the root cause.

The new fail-closed diagnostic runs after the first FFDec export and before floor verification. It verifies the SWF and script anchors. If the first export matches, it does not retry. On mismatch, it repeats the same FFDec export in a separate temporary directory, records both SHA256 hashes, sizes, newline counts, first differing byte offset, Java exit code and bounded logs, and fails regardless of whether the repeat matches. It never replaces source exports or updates committed anchors.

Classifications: first_export_matches_anchor; repeat_matches_anchor_first_does_not; repeatable_mismatch_against_anchor; two_distinct_mismatches_against_anchor; mismatch_repeat_unavailable. Only the first classification passes.

The diagnostic JSON is retained as a GitHub Actions artifact even on failure. No Flash visual/gameplay parity or Gymnasium/Kaggle readiness is inferred.

## Manifest-only drift guard (2026-10-31)

A correct first export can coexist with an incorrect manifest SHA256. Previously, that case retried FFDec and could label the result `first_export_matches_anchor` while `provenance_verified` was false. The diagnostic now returns `manifest_hash_mismatch_first_export_matches_anchor` without retrying FFDec, preserving both the correct file-byte evidence and the manifest inconsistency. The CLI still exits nonzero, so neither a successful retry nor correct bytes alone unlock source provenance or game parity. A regression test asserts the classification, no subprocess retry, and closed gameplay/Kaggle gates.

## Fail-closed artifact on early validation errors (2026-10-31)

If committed JSON is malformed, the original SWF hash differs, or the anchored script path is invalid, the CLI now attempts to write `ffdec_script_drift_diagnostic.json` before exiting with status 2. This diagnostic-only object records `classification=diagnostic_unavailable`, a bounded error message, and explicit false values for provenance, gameplay parity and Kaggle. It does not retry FFDec on an invalid SWF. If the report destination itself cannot be written, the command still exits nonzero; the Actions log is then the fallback evidence. Two CLI regression tests cover malformed JSON and a changed SWF.

## Malformed JSON container fail-closed regression (2026-10-31)

A syntactically valid JSON array at the committed-source or FFDec-manifest root, or an array in `manifest.original`, previously raised an uncaught `AttributeError` during `.get()` access. The CLI could exit without writing the diagnostic artifact. Validate these container types before accessing metadata, raise a bounded `ValueError`, and preserve `classification=diagnostic_unavailable` with all provenance/gameplay/Kaggle gates false. The regression test exercises all three cases through the CLI and prohibits an FFDec retry. This changes error reporting only; it does not prove Flash gameplay parity or resolve intermittent export drift.

## Independent export mismatch observed (2026-11-12)

Evidence: [SWF Audit run 43298527269, attempt 1](https://github.com/mjw3177109/motafukepygame/actions/runs/43298527269/attempts/1) failed at the independent-export comparison. Both exports contained 911 files from original SWF SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`, but `scripts/frame_4346/DoAction.as` and `scripts/frame_4346/DoAction_4.as` differed byte-for-byte. The job retained [failure artifact 13979613386](https://github.com/mjw3177109/motafukepygame/actions/runs/43298527269/artifacts/13979613386). A successful retry is not proof that the initial mismatch was harmless.

The subsequent evidence-preservation change `31ca1056` was checked in [SWF Audit run 43307471258](https://github.com/mjw3177109/motafukepygame/actions/runs/43307471258): two fresh independent exports again contained 911 files, with `only_first=[]`, `only_second=[]`, `changed=[]`, `identical=true`. [Python CI run 43307471274](https://github.com/mjw3177109/motafukepygame/actions/runs/43307471274) passed 542 Python tests. This confirms the diagnostic preservation workflow can complete on a matching run, **not** that the intermittent mismatch is resolved.

Next investigation: on the next mismatch, inspect the two preserved `DoAction.as` and `DoAction_4.as` versions from the same job, compute a bounded unified diff and first differing byte offset, and classify differences as formatting/decompiler output versus altered control flow or constants only after inspecting actual source text. Keep the byte-for-byte gate strict. Do not update committed anchors, claim original runtime parity, or open RL/Kaggle gates based on a passing retry.
