import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stepMoveArrow, DELTAS} from '../web/movement_probe.mjs';
const cases=JSON.parse(readFileSync(new URL('./fixtures/movement_probe_cases.json',import.meta.url),'utf8'));
function makeState(c) {
  const [row,col]=c.start ?? [5,5];
  const grid=Array.from({length:11},()=>Array(11).fill(0));
  const [dr,dc]=DELTAS[c.arrow];
  const nr=row+dr,nc=col+dc;
  if (nr>=0 && nr<11 && nc>=0 && nc<11) grid[nr][nc]=c.tile;
  if (Object.hasOwn(c,'origin_tile')) grid[row][col]=c.origin_tile;
  return {grid,row,col,hp:1000,attack:10,defense:10,keys:{yellow:0,blue:0,red:0,...c.keys}};
}
for (const c of cases) test(c.name,()=>{
  const state=makeState(c), original=JSON.stringify(state);
  if (c.error) {
    assert.throws(()=>stepMoveArrow(state,c.arrow),/needs original event/);
    return;
  }
  const {state:out,event}=stepMoveArrow(state,c.arrow);
  assert.equal(event,c.event);
  assert.deepEqual([out.row,out.col],c.position);
  for (const [key,amount] of Object.entries(c.key_delta??{})) assert.equal(out.keys[key],state.keys[key]+amount);
  for (const [stat,amount] of Object.entries(c.stat_delta??{})) assert.equal(out[stat],state[stat]+amount);
  if (c.cleared) {
    const [dr,dc]=DELTAS[c.arrow];
    assert.equal(out.grid[state.row+dr][state.col+dc],0);
  }
  if (Object.hasOwn(c,'origin_after')) assert.equal(out.grid[state.row][state.col],c.origin_after);
  if (Object.hasOwn(c,'target_after')) {
    const [dr,dc]=DELTAS[c.arrow];
    assert.equal(out.grid[state.row+dr][state.col+dc],c.target_after);
  }
  assert.equal(JSON.stringify(state),original);
});
test('invalid grid rejected',()=>{
  const state=makeState(cases[0]); state.grid.pop();
  assert.throws(()=>stepMoveArrow(state,1),/11x11/);
});
