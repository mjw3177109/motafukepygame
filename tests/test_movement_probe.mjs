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

test('reject sparse, inherited and unsafe grid slots before movement',()=>{
  for (const kind of ['missing_row','missing_cell','inherited_cell','unsafe_cell']) {
    const state=makeState(cases[0]);
    if (kind==='missing_row') delete state.grid[2];
    if (kind==='missing_cell') delete state.grid[2][4];
    if (kind==='inherited_cell') {
      delete state.grid[2][4];
      const proto=Object.create(Array.prototype);
      proto[4]=0;
      Object.setPrototypeOf(state.grid[2],proto);
    }
    if (kind==='unsafe_cell') state.grid[2][4]=Number.MAX_SAFE_INTEGER+1;
    const before=JSON.stringify(state);
    assert.throws(()=>stepMoveArrow(state,2),/11x11/);
    assert.equal(JSON.stringify(state),before,'input must remain unchanged');
    if (kind==='missing_row') assert.equal(Object.hasOwn(state.grid,2),false);
    if (kind==='missing_cell' || kind==='inherited_cell')
      assert.equal(Object.hasOwn(state.grid[2],4),false);
  }
});

test('reject malformed inventory before key pickup without mutation',()=>{
  const invalid=[
    null, [], {yellow:0,blue:0},
    {yellow:true,blue:0,red:0},
    {yellow:'1',blue:0,red:0},
    {yellow:Number.MAX_SAFE_INTEGER+1,blue:0,red:0},
  ];
  for (const keys of invalid) {
    const state=makeState(cases[5]);state.keys=keys;
    const before=structuredClone(state);
    assert.throws(()=>stepMoveArrow(state,2),/key inventory/);
    assert.deepEqual(state,before);
  }
  const inherited=Object.create({yellow:0});
  Object.assign(inherited,{blue:0,red:0});
  const state=makeState(cases[5]);state.keys=inherited;
  assert.throws(()=>stepMoveArrow(state,2),/key inventory/);
  assert.equal(Object.hasOwn(state.keys,'yellow'),false);
});
test('key pickup cannot overflow JavaScript safe integer',()=>{
  const state=makeState(cases[5]);state.keys.yellow=Number.MAX_SAFE_INTEGER;
  const before=structuredClone(state);
  assert.throws(()=>stepMoveArrow(state,2),/key inventory overflow/);
  assert.deepEqual(state,before);
});
