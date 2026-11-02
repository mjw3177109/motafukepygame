import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {classifyArrowInput,stepArrowTurn,replayArrowTurns} from '../web/arrow_turn_probe.mjs';
import {DELTAS} from '../web/movement_probe.mjs';

const cases=JSON.parse(readFileSync(new URL('./fixtures/arrow_turn_cases.json',import.meta.url),'utf8'));
const monsters={'0':[50,20,1,1,1,'绿头怪']};
function worldFor(c) {
  const grid=Array.from({length:11},()=>Array(11).fill(0));
  const [dr,dc]=DELTAS[c.arrow];grid[5+dr][5+dc]=c.tile;
  return {grid,row:5,col:5,hp:100,attack:51,defense:10,life:0,line:1,money:0,mp:0,
    keys:{yellow:0,blue:0,red:0,...c.keys},key_flag:1,display_list:0,display_jump:0,
    display_text:0,display_buy:0,display_kill:0,...c.hero,...c.flags};
}
for (const c of cases) test('original arrow '+c.name,()=>{
  const world=worldFor(c),before=structuredClone(world);
  if (c.error) assert.throws(()=>stepArrowTurn(world,c.arrow,monsters,c.rolls??[]),new RegExp(c.error));
  else {
    const result=stepArrowTurn(world,c.arrow,monsters,c.rolls??[]),state=result.state,expected=c.expected;
    assert.equal(result.event,expected.event);
    assert.deepEqual([state.row,state.col],expected.position);
    for (const key of ['key_flag','display_text','open_room','hp','attack','money','mp'])
      if (Object.hasOwn(expected,key)) assert.equal(state[key],expected[key]);
    if (Object.hasOwn(expected,'yellow')) assert.equal(state.keys.yellow,expected.yellow);
    if (Object.hasOwn(expected,'target_tile')) {
      const [dr,dc]=DELTAS[c.arrow];assert.equal(state.grid[5+dr][5+dc],expected.target_tile);
    }
    if (Object.hasOwn(expected,'rolls_used')) assert.equal(result.rolls_used,expected.rolls_used);
  }
  assert.deepEqual(world,before);
});
test('text and door animation gates are not auto-dismissed',()=>{
  const pickup=worldFor(cases[2]);
  const a=replayArrowTurns(pickup,[{arrow_id:2},{arrow_id:2}],monsters);
  assert.deepEqual(a.trace.map(t=>t.event),['pickup_yellow_key','input_blocked']);
  assert.equal(a.state.row,5);assert.equal(a.state.keys.yellow,1);assert.equal(pickup.grid[5][6],6);
  const door=worldFor(cases[3]);
  const b=replayArrowTurns(door,[{arrow_id:2},{arrow_id:2}],monsters);
  assert.deepEqual(b.trace.map(t=>t.event),['open_yellow_door','input_blocked']);
  assert.equal(b.state.open_room,1);assert.deepEqual([b.state.last_x,b.state.last_y],[5,6]);
});
test('pure walking replay and malformed flags fail closed',()=>{
  const world=worldFor(cases[0]);
  const r=replayArrowTurns(world,[{arrow_id:2},{arrow_id:2}],monsters);
  assert.deepEqual(r.trace.map(t=>t.event),['move','move']);
  assert.deepEqual([r.state.row,r.state.col],[5,7]);
  assert.deepEqual([world.row,world.col],[5,5]);
  assert.throws(()=>classifyArrowInput({key_flag:1},2),/flags/);
  assert.throws(()=>classifyArrowInput(world,5),/arrow_id/);
});
