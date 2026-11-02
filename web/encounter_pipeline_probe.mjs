/** Deterministic composition probe. Not a playable game or frame clock. */
import {startEncounter} from './encounter_start_probe.mjs';
import {replayToVictory} from './battle_timeline_probe.mjs';
import {frame54Handoff,consumeBattleCompletion} from './battle_settlement_probe.mjs';

export function resolveEncounter(world, arrowId, monsters, criticalRolls, maxActions=10000) {
  if (!world || world.display_kill !== 0) throw new Error('pipeline requires idle display_kill=0; input gate remains unverified');
  if (!Array.isArray(criticalRolls)) throw new Error('critical_rolls must be an explicit list');
  const start=startEncounter(world,arrowId,monsters);
  const events=[{stage:'encounter',event:start.event,sound:start.sound}];
  if (start.event==='encounter_blocked') {
    if (criticalRolls.length) throw new Error('blocked encounter cannot consume critical rolls');
    return {state:start.state,events,preview:start.preview,battle:null,steps:[],cleared:[]};
  }
  const replay=replayToVictory(start.battle,criticalRolls,maxActions);
  events.push({stage:'battle',event:'frame35_reached',actions:replay.steps.length,rolls_used:replay.rolls_used});
  const handoff=frame54Handoff(start.state,replay.battle);
  events.push({stage:'handoff',event:handoff.event});
  const monster=monsters[String(start.preview.enemy_id)];
  const reward=consumeBattleCompletion(handoff.state,monster);
  events.push({stage:'settlement',event:reward.event,sound:reward.sound});
  return {state:reward.state,events,preview:start.preview,battle:replay.battle,steps:replay.steps,cleared:reward.cleared};
}
