# SWF source audit trigger regression (2026-10-30)

The previous `swf-audit.yml` ran on pushes to a single feature branch only when `game.swf`, `FFDec/**`, `tools/**`, or the workflow itself changed. A commit that changed `data/original_floors.json` without touching those paths did **not** trigger the original ActionScript-to-map provenance check. Pull requests from other branches were also not covered by this workflow.

This patch uses identical explicit path filters for the existing feature-branch push event and a new pull-request event. The filter now includes `data/original_floors.json` and `core/floor_tile_plan.py`, as well as the test that guards the trigger. The source verification command, Java 8 FFDec export, asset gap audit, and case-safe artifact archive are unchanged.

Run `python -m unittest discover -s tests -v` to verify the trigger structure. A GitHub Actions `success` proves the audited static floor data matches FFDec extraction, **not** visual, event, ending, or playable parity. The PR must remain unmerged until its checks and manual review pass. Gymnasium and Kaggle remain blocked.

## Real static-preview dependency trigger coverage (2026-10-31)

The real FFDec SVG smoke tests import the Pygame loader and preview renderer
(`core/static_svg_assets.py`, `core/verified_static_preview.py`, and
`core/floor_render.py`). Previously, changing these files or their direct
regression tests did not trigger `SWF Original Audit` because the path filters
only covered the corresponding web modules. The normal Python unit workflow
still ran, but that is not a substitute for the original-SWF Pygame/Chromium
smoke tests.

Both push and PR filters now include those three Python modules and their
three matching Python tests. Two original-render smoke test files that were
previously in push but missing from PR filters are also included in PR.
A regression test checks that both path lists are identical and contain no
duplicates. This is a CI coverage fix, **not** a change to the game renderer
or evidence of 1:1 parity.
