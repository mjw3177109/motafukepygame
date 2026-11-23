# FFDec case-sensitive export preservation

The SWF Original Audit job previously uploaded the entire FFDec export directory through GitHub Actions `upload-artifact@v4`. Its 2026-10-31 run 41149139150 logged **case-insensitive filename collisions** for original button ActionScript files such as `on(keyPress j).as` and `on(keyPress J).as`. Uploading the raw directory can replace one with the other, losing evidence needed for 1:1 event reconstruction.

The job now verifies every exported file against `manifest.json`, packs the original case-sensitive names into a single `ffdec_export.tar.gz`, opens that archive again, and verifies every member's size and SHA256. A separate `export_archive_report.json` records collision groups and the archive SHA256. The GitHub artifact uploads the archive and reports, **not** the raw export directory.

To inspect: download `original-flash-audit` from the SWF Original Audit run, compare the SHA256 of `ffdec_export.tar.gz` with `export_archive_report.json`, then extract the archive on a case-sensitive filesystem or inspect members with `tar -tzf ffdec_export.tar.gz`. On case-insensitive systems, inspect the archive without extracting overlapping paths.

The report is evidence-preservation only; it does **not** establish any sprite binding, visual parity, gameplay parity, or Kaggle readiness.
