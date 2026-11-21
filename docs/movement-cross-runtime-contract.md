# Python / HTML5 movement probe contract

This test closes a narrow integration gap: the Python and JavaScript movement probes previously ran against the same JSON fixture independently, but CI did not compare their complete outputs to each other.

## What is compared

`tests/test_movement_cross_runtime.py` loads the existing shared vector set in `tests/fixtures/movement_probe_cases.json`, constructs the same 11×11 state for both implementations, and invokes the browser-side ES module with Node.js.

For every vector it compares:

- the complete emitted event name;
- the complete resulting state, including all 121 grid cells, hero coordinates, stats and key counts;
- whether the caller's input snapshot remained unchanged;
- fail-closed behavior for the fixture's explicitly unsupported stair and monster tiles.

The test does not normalize away state differences and does not treat an unsupported tile as a successful move. Error wording is intentionally not compared because Python and JavaScript expose different exception classes.

## Scope boundary

This is **cross-runtime probe parity for the currently implemented subset**, not a claim of original Flash gameplay parity. The vector fixture is not a full original-game recording. Keyboard/modal gates, movement animation timing, stairs, monsters, combat, scripts, floor transitions, rendering and game completion remain outside this contract. Those features must be added only with source-backed vectors and their own original-Flash evidence.

The Python unittest discovery step runs this contract in GitHub Actions. Node.js is already required by the existing JavaScript probe test steps; on a developer machine without Node.js this one integration test is skipped with an explicit reason.
