/** Original button-gate and arrow-turn composition; not a playable UI. */
import {DELTAS, stepMoveArrow} from './movement_probe.mjs';
import {resolveEncounter} from './encounter_pipeline_probe.mjs';

export function classifyArrowInput(world, arrowId) {
  if (!Number.isSafeInteger(arrowId) || !Object.hasOwn(DELTAS, arrowId))
    throw new Error('arrow_id must be one of Flash 1,2,3,4');
  const flags=['key_flag','display_list','display_jump','display_text','display_buy'];
  if (!world || flags.some(f=>!Number.isSafeInteger(world[f])))
    throw new Error('original keyboard gate flags required');
  if (world.key_flag===1 && world.display_list===0 && world.display_jump===0 && world.display_text===0)
    return 'move_arrow';
  if ([3,4].includes(arrowId) && world.display_buy===1) return 'buy_modal_unimplemented';
  if ([3,4].includes(arrowId) && world.display_jump===1) return 'jump_modal_unimplemented';
  return 'input_blocked';
}

export function stepArrowTurn(world, arrowId, monsters, criticalRolls=[]) {
  if (!Array.isArray(criticalRolls)) throw new Error('critical_rolls must be an explicit list');
  const gate=classifyArrowInput(world,arrowId);
  if (gate.endsWith('_unimplemented')) throw new Error(gate);
  if (gate==='input_blocked') {
    if (criticalRolls.length) throw new Error('blocked input cannot consume critical rolls');
    return {state:structuredClone(world),event:gate,events:[{stage:'keyboard',event:gate}],rolls_used:0,cleared:[]};
  }
  if (world.display_kill!==0) throw new Error('arrow router requires idle display_kill=0');
  const {row,col,grid}=world;
  if (![row,col].every(Number.isSafeInteger) || row<0 || row>=11 || col<0 || col>=11)
    throw new Error('invalid original row/column');
  if (!Array.isArray(grid) || grid.length!==11 || grid.some(line=>!Array.isArray(line) || line.length!==11 || !line.every(Number.isSafeInteger)))
    throw new Error('expected original 11x11 integer grid');
  const [dr,dc]=DELTAS[arrowId],nr=row+dr,nc=col+dc;
  const tile=nr>=0 && nr<11 && nc>=0 && nc<11 ? grid[nr][nc] : null;
  if (tile!==null && ((tile>=40 && tile<=70) || tile===188 || tile===198)) {
    const result=resolveEncounter(world,arrowId,monsters,criticalRolls);
    const used=result.events.find(e=>e.stage==='battle')?.rolls_used ?? 0;
    return {state:result.state,event:result.events.at(-1).event,events:result.events,rolls_used:used,cleared:result.cleared};
  }
  if (criticalRolls.length) throw new Error('non-monster movement cannot consume critical rolls');
  const result=stepMoveArrow(world,arrowId),state=result.state,event=result.event;
  if (event.startsWith('pickup_')) {state.key_flag=0;state.display_text=1;}
  else if (event.startsWith('open_')) {
    state.key_flag=0;state.open_room=1;state.last_x=nr;state.last_y=nc;
  }
  return {state,event,events:[{stage:'move_arrow',event}],rolls_used:0,cleared:[]};
}

export function replayArrowTurns(world, actions, monsters) {
  if (!Array.isArray(actions)) throw new Error('actions must be a list');
  let state=structuredClone(world);
  const trace=[];
  for (const [step,action] of actions.entries()) {
    if (!action || typeof action!=='object' || Array.isArray(action)) throw new Error('each action must be an object');
    const result=stepArrowTurn(state,action.arrow_id,monsters,action.critical_rolls??[]);
    state=result.state;
    trace.push({step,arrow_id:action.arrow_id,event:result.event,rolls_used:result.rolls_used,state:structuredClone(state)});
  }
  return {state,trace};
}
