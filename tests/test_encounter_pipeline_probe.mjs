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


// Source-roster full encounter -> frame35 -> frame54 -> reward regression.
// Hero stats/rolls/grid are synthetic; no original Flash replay is claimed.
const fullRoster=JSON.parse(readFileSync(new URL('../data/original_combat_tables.json',import.meta.url),'utf8'));
test('all 33 original monsters: one-hit and two-hit full pipeline (66 synthetic scenarios)',()=>{
  assert.equal(fullRoster.gameplay_parity_verified,false);
  assert.equal(fullRoster.gymnasium_ready,false);
  assert.deepEqual(Object.keys(fullRoster.monsters).sort((a,b)=>Number(a)-Number(b)),
    Array.from({length:33},(_,i)=>String(i)));
  for(let enemyId=0;enemyId<33;enemyId++) {
    const monster=fullRoster.monsters[String(enemyId)];
    for(const twoHit of [false,true]) {
      const grid=Array.from({length:11},()=>Array(11).fill(0));
      for(let r=3;r<=5;r++)for(let c=5;c<=7;c++)grid[r][c]=7;
      grid[0][0]=17;
      grid[5][6]=enemyId<31?enemyId+40:enemyId===31?188:198;
      const world={grid,row:5,col:5,hp:1000000,
        attack:monster[2]+monster[0]-(twoHit?1:0),
        defense:monster[1]-(twoHit?7:0),
        life:0,line:1,display_kill:0,key_flag:1,money:11,mp:13};
      const before=structuredClone(world);
      const result=resolveEncounter(world,2,{[String(enemyId)]:monster},twoHit?[199,199]:[199]);
      const special=enemyId===20?100:enemyId===12?300:enemyId===10?250000:enemyId===17?333333:0;
      const expectedHp=1000000-special-(twoHit?7:0);
      const cleared=enemyId===31||enemyId===32?
        Array.from({length:9},(_,i)=>[3+Math.floor(i/3),5+i%3]):[[5,6]];
      assert.deepEqual(world,before,'world mutated for monster '+enemyId);
      assert.deepEqual(result.cleared,cleared,'clearance for monster '+enemyId);
      assert.equal(result.state.hp,expectedHp,'HP for monster '+enemyId);
      assert.equal(result.battle.right_hp,expectedHp);
      assert.equal(result.battle.left_hp,0);
      assert.equal(result.state.money,11+monster[3]);
      assert.equal(result.state.mp,13+monster[4]);
      assert.equal(result.state.display_kill,0);
      assert.equal(result.state.grid[0][0],17);
      assert.equal(result.state.grid[3][5],enemyId>=31?0:7);
      assert.equal(result.state.grid[5][6],0);
      assert.equal(result.steps.length,twoHit?3:1);
      assert.equal(result.steps.filter(s=>s.event==='monster_counterattack').length,twoHit?1:0);
      assert.deepEqual(result.events.map(e=>e.event),
        ['encounter_started','frame35_reached','frame54_handoff','battle_reward']);
      assert.equal(result.state.boss_kills,enemyId===19?1:undefined);
    }
  }
});
