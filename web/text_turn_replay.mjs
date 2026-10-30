/** Explicit replay of evidenced arrow turns and text sprite events, not a clock. */
import {stepArrowTurn} from './arrow_turn_probe.mjs';
import {stepTextLifecycle} from './text_lifecycle_probe.mjs';

export function replayTextTurns(world, actions, monsters, arrowStep=stepArrowTurn) {
  if (!world || typeof world!=='object' || Array.isArray(world) || !Array.isArray(actions))
    throw new Error('world must be an object and actions must be a list');
  let state=structuredClone(world);
  const trace=[];
  let gameOverRequested=false;
  for (const [step,action] of actions.entries()) {
    if (gameOverRequested)
      throw new Error('game_over requested; subsequent inputs require an implemented ending');
    if (!action || typeof action!=='object' || Array.isArray(action) || typeof action.type!=='string')
      throw new Error('each action must have a type');
    const kind=action.type;
    let result, effects=[];
    if (kind==='arrow') {
      if (Object.keys(action).some(k=>!['type','arrow_id','critical_rolls'].includes(k)))
        throw new Error('unsupported arrow action fields');
      result=arrowStep(state,action.arrow_id,monsters,action.critical_rolls??[]);
    } else if (kind==='text_frame32' || kind==='text_cleanup') {
      if (Object.keys(action).length!==1)
        throw new Error('text sprite actions do not take arrow inputs or rolls');
      result=stepTextLifecycle(state,kind==='text_frame32'?'frame32':'cleanup');
      effects=result.effects;
    } else {
      throw new Error('unsupported action type: '+kind);
    }
    state=result.state;
    gameOverRequested=effects.includes('goto_game_over');
    trace.push({step,type:kind,event:result.event,effects,state:structuredClone(state)});
  }
  return {state,trace,game_over_requested:gameOverRequested};
}
