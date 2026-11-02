import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stepJumpSelection} from '../web/jump_selection_probe.mjs';
const cases=JSON.parse(readFileSync(new URL('./fixtures/jump_selection_cases.json',import.meta.url),'utf8'));
const WORLD={key_flag:0,display_list:0,display_jump:1,display_text:0,display_buy:0,now_line:1};
for (const c of cases) test('jump cursor '+c.name,()=>{
  const world=structuredClone(WORLD), cursor={now_move_id:c.start,moves_x:120,moves_y:200,move_x:40};
  const result=stepJumpSelection(world,cursor,c.arrow_id);
  assert.equal(result.cursor.now_move_id,c.end);
  assert.equal(result.cursor.moves_x,120+c.dx);
  assert.equal(result.cursor.moves_y,200+c.dy);
  assert.deepEqual(result.effects,['play_sound:music_11']);
  assert.deepEqual(result.state,WORLD);
  assert.deepEqual(world,WORLD);
  assert.equal(cursor.now_move_id,c.start);
});
test('invalid modal, index, arrow and coordinates fail closed',()=>{
  const cursor={now_move_id:1,moves_x:120,moves_y:200,move_x:40};
  for(const world of [{...WORLD,display_jump:0},{...WORLD,display_buy:1}])
    assert.throws(()=>stepJumpSelection(world,cursor,3),/inactive or shop/);
  for(const index of [0,21,true,null])
    assert.throws(()=>stepJumpSelection(WORLD,{...cursor,now_move_id:index},3),/index must/);
  for(const arrow of [1,2,true,'3'])
    assert.throws(()=>stepJumpSelection(WORLD,cursor,arrow),/Up/);
  for(const x of [NaN,Infinity,true])
    assert.throws(()=>stepJumpSelection(WORLD,{...cursor,moves_x:x},3),/finite numeric/);
  assert.throws(()=>stepJumpSelection({...WORLD,display_text:null},cursor,3),/gate flags/);
});
