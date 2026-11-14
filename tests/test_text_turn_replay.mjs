import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {replayTextTurns} from '../web/text_turn_replay.mjs';
const cases=JSON.parse(fs.readFileSync(new URL('./fixtures/text_turn_replay_cases.json',import.meta.url),'utf8'));
function worldFor(c) {
  const grid=Array.from({length:11},()=>Array(11).fill(0));grid[5][6]=c.tile;
  const world={grid,row:5,col:5,hp:100,attack:51,defense:10,life:0,line:1,money:0,mp:0,
    keys:{yellow:0,blue:0,red:0},key_flag:1,display_list:0,display_jump:0,display_text:0,
    display_buy:0,display_kill:0,boss_kills:0,floor26_cell_3_5:188,...(c.flags??{})};
  if(c.omit_floor26_cell) delete world.floor26_cell_3_5;
  return world;
}
for(const c of cases) test('text turn '+c.name,()=>{
  const world=worldFor(c),before=structuredClone(world);
  if(c.error) assert.throws(()=>replayTextTurns(world,c.actions,{}),new RegExp(c.error));
  else {
    const result=replayTextTurns(world,c.actions,{});
    assert.deepEqual(result.trace.map(x=>x.event),c.events);
    assert.deepEqual([result.state.row,result.state.col],c.position);
    assert.equal(result.state.key_flag,c.key_flag);
    assert.equal(result.state.display_text,c.display_text);
    assert.equal(result.state.keys.yellow,c.yellow);
    assert.equal(result.game_over_requested,c.game_over_requested);
    if(result.game_over_requested) assert.ok(result.trace.at(-1).effects.includes('goto_game_over'));
  }
  assert.deepEqual(world,before);
});
