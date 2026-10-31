# FFDec ActionScript export drift diagnosis (2026-10-31)

PR #1 run 41237985460 attempt 1 failed on the anchored hash for export/scripts/frame_4346/DoAction_2.as. Attempt 2 passed. This proves differing observed outcomes, not the root cause.

The new fail-closed diagnostic runs after the first FFDec export and before floor verification. It verifies the SWF and script anchors. If the first export matches, it does not retry. On mismatch, it repeats the same FFDec export in a separate temporary directory, records both SHA256 hashes, sizes, newline counts, first differing byte offset, Java exit code and bounded logs, and fails regardless of whether the repeat matches. It never replaces source exports or updates committed anchors.

Classifications: first_export_matches_anchor; repeat_matches_anchor_first_does_not; repeatable_mismatch_against_anchor; two_distinct_mismatches_against_anchor; mismatch_repeat_unavailable. Only the first classification passes.

The diagnostic JSON is retained as a GitHub Actions artifact even on failure. No Flash visual/gameplay parity or Gymnasium/Kaggle readiness is inferred.

## Manifest-only drift guard (2026-10-31)

A correct first export can coexist with an incorrect manifest SHA256. Previously, that case retried FFDec and could label the result `first_export_matches_anchor` while `provenance_verified` was false. The diagnostic now returns `manifest_hash_mismatch_first_export_matches_anchor` without retrying FFDec, preserving both the correct file-byte evidence and the manifest inconsistency. The CLI still exits nonzero, so neither a successful retry nor correct bytes alone unlock source provenance or game parity. A regression test asserts the classification, no subprocess retry, and closed gameplay/Kaggle gates.
