import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {startEncounter} from '../web/encounter_start_probe.mjs';
const cases=JSON.parse(readFileSync(new URL('./fixtures/encounter_start_cases.json',import.meta.url),'utf8'));
function worldFor(v) {const grid=Array.from({length:11},()=>Array(11).fill(0));grid[5][6]=v.tile;return {grid,row:5,col:5,...v.hero,display_kill:0,key_flag:1};}
for (const v of cases) test(v.name,()=>{
  const world=worldFor(v),before=JSON.stringify(world);
  const result=startEncounter(world,2,{[v.enemy_id]:v.monster});
  assert.equal(result.event,v.event);
  assert.equal(result.state.hp,v.hp_after);
  assert.equal(result.sound,v.sound);
  assert.equal(result.preview.enemy_id,v.enemy_id);
  assert.equal(result.state.boss_kills??null,v.boss_kills??null);
  assert.equal(result.state.grid[5][6],v.tile);
  assert.deepEqual([result.state.row,result.state.col],[5,5]);
  if (v.event==='encounter_started') {
    assert.equal(result.state.display_kill,1);
    assert.equal(result.state.key_flag,0);
    assert.deepEqual([result.state.boss_row,result.state.boss_col],[5,6]);
    assert.equal(result.battle.right_hp,v.hp_after);
    assert.equal(result.battle.life,v.hero.life);
  } else {assert.equal(result.battle,null);assert.equal(result.state.display_kill,0);}
  assert.equal(JSON.stringify(world),before);
});
test('unverified target fails closed',()=>{const w=worldFor(cases[0]);w.grid[5][6]=13;assert.throws(()=>startEncounter(w,2,{}),/not an original monster/);});
test('missing monster table fails closed',()=>assert.throws(()=>startEncounter(worldFor(cases[0]),2,{}),/missing verified monster/));
