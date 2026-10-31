# SWF source audit trigger regression (2026-10-30)

The previous `swf-audit.yml` ran on pushes to a single feature branch only when `game.swf`, `FFDec/**`, `tools/**`, or the workflow itself changed. A commit that changed `data/original_floors.json` without touching those paths did **not** trigger the original ActionScript-to-map provenance check. Pull requests from other branches were also not covered by this workflow.

This patch uses identical explicit path filters for the existing feature-branch push event and a new pull-request event. The filter now includes `data/original_floors.json` and `core/floor_tile_plan.py`, as well as the test that guards the trigger. The source verification command, Java 8 FFDec export, asset gap audit, and case-safe artifact archive are unchanged.

Run `python -m unittest discover -s tests -v` to verify the trigger structure. A GitHub Actions `success` proves the audited static floor data matches FFDec extraction, **not** visual, event, ending, or playable parity. The PR must remain unmerged until its checks and manual review pass. Gymnasium and Kaggle remain blocked.
