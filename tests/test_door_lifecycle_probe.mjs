import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {stepDoorLifecycle} from '../web/door_lifecycle_probe.mjs';
import {stepArrowTurn} from '../web/arrow_turn_probe.mjs';
const cases=JSON.parse(fs.readFileSync(new URL('./fixtures/door_lifecycle_cases.json',import.meta.url),'utf8'));
function worldFor(c) {
  const grid=Array.from({length:11},()=>Array(11).fill(0));grid[5][6]=c.tile??0;
  const keys={yellow:0,blue:0,red:0};if(c.key)keys[c.key]=1;
  return {grid,row:5,col:5,hp:100,attack:51,defense:10,life:0,line:1,money:0,mp:0,keys,
    key_flag:1,display_list:0,display_jump:0,display_text:0,display_buy:0,
    display_kill:0,open_room:0,last_x:5,last_y:6};
}
for(const c of cases)test('door '+c.name,()=>{
  const initial=worldFor(c);
  let before;
  if(c.tile!==undefined){
    const opened=stepArrowTurn(initial,2,{});
    assert.equal(opened.event,'open_'+c.key+'_door');
    assert.equal(opened.state.keys[c.key],0);
    assert.equal(opened.state.grid[5][6],0);
    assert.equal(stepArrowTurn(opened.state,2,{}).event,'input_blocked');
    before=opened.state;
  }else before={...structuredClone(initial),open_room:1,key_flag:0};
  const preserved=structuredClone(before);
  const ready=stepDoorLifecycle(before,'frame_complete',{sprite:c.sprite,frame:c.frame});
  assert.equal(ready.state.open_room,2);assert.equal(ready.state.key_flag,0);
  assert.deepEqual(before,preserved);
  const finished=stepDoorLifecycle(ready.state,'cleanup');
  assert.equal(finished.state.open_room,0);assert.equal(finished.state.key_flag,1);
  assert.deepEqual(finished.effects,['remove_map_sprite:mt_m_5_6']);
  assert.equal(ready.state.open_room,2);
  if(c.tile!==undefined){
    const moved=stepArrowTurn(finished.state,2,{});
    assert.equal(moved.event,'move');assert.deepEqual([moved.state.row,moved.state.col],[5,6]);
  }
});
test('door invalid phase/frame/coordinates fail closed',()=>{
  const state=worldFor(cases[0]);
  assert.throws(()=>stepDoorLifecycle(state,'cleanup'),/open_room=2/);
  state.open_room=1;state.key_flag=0;
  for(const [sprite,frame] of [['mt_15',10],['mt_02',5],['mt_99',10]])
    assert.throws(()=>stepDoorLifecycle(state,'frame_complete',{sprite,frame}),/unverified door sprite\/frame/);
  const ready=stepDoorLifecycle(state,'frame_complete',{sprite:'mt_02',frame:10}).state;
  assert.throws(()=>stepDoorLifecycle(ready,'frame_complete',{sprite:'mt_02',frame:10}),/open_room=1/);
  for(const x of [null,-1,11,true])
    assert.throws(()=>stepDoorLifecycle({...ready,last_x:x},'cleanup'),/Last_x\/Last_y/);
  assert.throws(()=>stepDoorLifecycle(ready,'cleanup',{sprite:'mt_02',frame:10}),/cleanup does not accept/);
});
