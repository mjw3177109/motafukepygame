import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {beginBattle} from '../web/battle_frame_probe.mjs';
import {replayToVictory} from '../web/battle_timeline_probe.mjs';
import {startEncounter} from '../web/encounter_start_probe.mjs';
import {frame54Handoff,consumeBattleCompletion} from '../web/battle_settlement_probe.mjs';

const cases=JSON.parse(readFileSync(new URL('./fixtures/battle_timeline_cases.json',import.meta.url),'utf8'));
for (const c of cases) test(c.name,()=>{
  const initial=beginBattle(c.monster,c.hero,c.life), before=structuredClone(initial);
  const result=replayToVictory(initial,c.rolls), exp=c.expected;
  assert.equal(result.next_frame,35);
  assert.equal(result.rolls_used,exp.rolls_used);
  assert.equal(result.steps.length,exp.actions);
  assert.equal(result.steps.filter(x=>x.event==='monster_counterattack').length,exp.counterattacks);
  assert.equal(result.battle.left_hp,exp.left_hp);
  assert.equal(result.battle.right_hp,exp.right_hp);
  assert.equal(result.battle.kill_number,exp.kill_number);
  assert.deepEqual(result.steps.map(x=>x.transition),exp.transitions);
  assert.deepEqual(initial,before);
});
test('rejects missing, surplus rolls and bounded incomplete run',()=>{
  const c=cases[0], battle=beginBattle(c.monster,c.hero,c.life);
  assert.throws(()=>replayToVictory(battle,[]),/missing/);
  assert.throws(()=>replayToVictory(battle,[199,199]),/unused/);
  assert.throws(()=>replayToVictory({...battle,kill_right:0},[199]),/positive/);
  const longer=cases[1];
  assert.throws(()=>replayToVictory(beginBattle(longer.monster,longer.hero,longer.life),longer.rolls,1),/max_actions/);
});
test('encounter -> frame34 victory -> frame54 -> reward without phantom retaliation',()=>{
  const monster=cases[0].monster,grid=Array.from({length:11},()=>Array(11).fill(0));
  grid[5][6]=40;
  const world={grid,row:5,col:5,hp:100,attack:11,defense:10,life:0,line:1,
    display_kill:0,key_flag:1,money:0,mp:0}, before=structuredClone(world);
  const started=startEncounter(world,2,{'0':monster});
  assert.equal(started.event,'encounter_started');
  const replay=replayToVictory(started.battle,[199]);
  assert.equal(replay.steps.length,1);
  const handoff=frame54Handoff(started.state,replay.battle);
  const reward=consumeBattleCompletion(handoff.state,monster);
  assert.deepEqual([reward.state.hp,reward.state.money,reward.state.mp],[100,1,1]);
  assert.equal(reward.state.grid[5][6],0);
  assert.equal(reward.state.display_kill,0);
  assert.deepEqual(world,before);
});
