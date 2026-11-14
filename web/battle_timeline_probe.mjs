/** Evidence-scoped frame24/frame34/frame35 branching, without frame timing. */
import {stepBattleFrame} from './battle_frame_probe.mjs';

export function replayToVictory(initialBattle, criticalRolls, maxActions=10000) {
  if (!initialBattle || initialBattle.kill_number !== 0) throw new Error('requires a fresh frame1 battle snapshot');
  if (!Number.isSafeInteger(initialBattle.left_hp) || initialBattle.left_hp <= 0) throw new Error('requires a living original monster');
  if (!Number.isSafeInteger(initialBattle.kill_right) || initialBattle.kill_right <= 0) throw new Error('requires positive verified hero damage');
  if (!Number.isSafeInteger(maxActions) || maxActions <= 0) throw new Error('max_actions must be a positive integer');
  if (!Array.isArray(criticalRolls) || !criticalRolls.every(v=>Number.isSafeInteger(v) && v>=0 && v<200)) {
    throw new Error('critical_rolls must be a list of Flash random(200) results');
  }
  let battle=structuredClone(initialBattle), rollsUsed=0;
  const steps=[];
  let completed=false;
  for (let i=0;i<maxActions;i++) {
    let roll=null;
    if (battle.kill_number % 2 === 0) {
      if (rollsUsed >= criticalRolls.length) throw new Error('missing a required original critical roll');
      roll=criticalRolls[rollsUsed++];
    }
    const result=stepBattleFrame(battle,roll);
    if (result.event==='idle') throw new Error('battle stalled before frame35');
    battle=result.state;
    const transition=result.jump_to_35?'frame24_to_35':battle.left_hp>0?'frame34_to_24':'frame34_to_35';
    steps.push({event:result.event,damage:result.damage,critical:result.critical,
      left_hp:battle.left_hp,right_hp:battle.right_hp,transition});
    if (transition!=='frame34_to_24') {completed=true;break;}
  }
  if (!completed) throw new Error('battle did not reach frame35 within max_actions');
  if (rollsUsed!==criticalRolls.length) throw new Error('unused critical rolls; exact replay evidence required');
  return {battle,steps,rolls_used:rollsUsed,next_frame:35};
}
