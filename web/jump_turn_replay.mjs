/** Deterministic jump-menu replay. Stops before unevidenced floor redraw. */
import { stepJumpLifecycle } from './jump_lifecycle_probe.mjs';
import { stepJumpSelection } from './jump_selection_probe.mjs';

const ALLOWED = new Set(['up', 'down', 'confirm', 'cancel', 'cleanup']);

export function replayJumpTurns(world, cursor, actions) {
  if (!world || typeof world !== 'object' || Array.isArray(world) ||
      !cursor || typeof cursor !== 'object' || Array.isArray(cursor) ||
      !Array.isArray(actions))
    throw new Error('world, cursor and actions must be object, object, list');
  let state = structuredClone(world), selection = structuredClone(cursor);
  const trace = [];
  let floorRefreshPending = false;
  for (const [index, action] of actions.entries()) {
    if (!action || typeof action !== 'object' || Array.isArray(action) ||
        Object.keys(action).length !== 1 || typeof action.type !== 'string')
      throw new Error('jump action must contain only a string type');
    const kind = action.type;
    if (!ALLOWED.has(kind)) throw new Error('unsupported jump action: ' + kind);
    if (floorRefreshPending)
      throw new Error('SetLineDisplay(1) requested; floor redraw not implemented');
    let result;
    if (kind === 'up' || kind === 'down') {
      result = stepJumpSelection(state, selection, kind === 'up' ? 3 : 4);
      state = result.state;
      selection = result.cursor;
    } else {
      result = stepJumpLifecycle(state, kind === 'confirm' ? selection : null, kind);
      state = result.state;
    }
    floorRefreshPending = result.effects.includes('set_line_display:1');
    trace.push({step: index, type: kind, event: result.event,
      effects: structuredClone(result.effects), state: structuredClone(state),
      cursor: structuredClone(selection), floor_refresh_pending: floorRefreshPending});
  }
  return {state, cursor: selection, trace, floor_refresh_pending: floorRefreshPending};
}
