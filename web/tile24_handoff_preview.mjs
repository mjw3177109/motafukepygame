/** Read-only tile-24 handoff preview; NEVER executes dialogue or mutates the game.
 * Review state is caller-supplied, not inferred from the movement world.
 * Unlike the Python counterpart, this JS review does NOT audit ActionScript.
 */
import {stepArrowTurn, Tile24HandoffRequired} from './arrow_turn_probe.mjs';
import {traceTile24State} from './tile24_state_probe.mjs';

export function previewTile24Handoff(world, arrowId, monsters, reviewState) {
  let target;
  try {
    stepArrowTurn(world, arrowId, monsters, []);
  } catch (error) {
    if (!(error instanceof Tile24HandoffRequired)) throw error;
    target = [...error.target];
  }
  if (!target) throw new Error('no tile-24 handoff for this input');
  if (!reviewState || typeof reviewState !== 'object' ||
      Array.isArray(reviewState) || reviewState.tile_id !== 24)
    throw new Error('explicit tile-24 review state required');
  const review = traceTile24State(reviewState);
  return {
    event: 'tile24_review_only',
    target,
    review,
    state_mapping_verified: false,
    flash_runtime_verified: false,
    executable: false,
    gymnasium_ready: false,
  };
}
