import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolveEncounter} from '../web/encounter_pipeline_probe.mjs';

const cases=JSON.parse(readFileSync(new URL('./fixtures/encounter_pipeline_cases.json',import.meta.url),'utf8'));
function makeWorld(c) {
  const grid=Array.from({length:11},()=>Array(11).fill(0));
  grid[5][6]=c.tile;
  return {grid,row:5,col:5,...c.hero,display_kill:0,key_flag:1,money:0,mp:0};
}
for (const c of cases) test('original pipeline '+c.name,()=>{
  const world=makeWorld(c),before=structuredClone(world);
  const result=resolveEncounter(world,2,{[String(c.tile-40)]:c.monster},c.rolls);
  assert.equal(result.events.at(-1).event,c.expected.event);
  for (const key of ['hp','money','mp','display_kill']) assert.equal(result.state[key],c.expected[key]);
  assert.equal(result.steps.length,c.expected.actions);
  assert.equal(result.steps.filter(s=>s.event==='monster_counterattack').length,c.expected.counterattacks);
  assert.deepEqual(result.cleared,c.expected.cleared);
  assert.equal(result.state.grid[5][6],c.expected.cleared.length?0:c.tile);
  assert.deepEqual(world,before);
});
test('pipeline rejects missing rolls, busy state and surplus blocked rolls',()=>{
  const c=cases[0],world=makeWorld(c);
  assert.throws(()=>resolveEncounter(world,2,{'0':c.monster},[]),/missing/);
  assert.throws(()=>resolveEncounter({...world,display_kill:1},2,{'0':c.monster},[199]),/idle/);
  const blocked=cases[2];
  assert.throws(()=>resolveEncounter(makeWorld(blocked),2,{'0':blocked.monster},[199]),/blocked/);
});
