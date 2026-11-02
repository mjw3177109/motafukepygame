import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stepJumpLifecycle} from '../web/jump_lifecycle_probe.mjs';
const cases=JSON.parse(readFileSync(new URL('./fixtures/jump_lifecycle_cases.json',import.meta.url),'utf8'));
for(const c of cases) test('jump lifecycle '+c.name,()=>{
  const world={display_jump:c.mode,key_flag:c.key,now_line:c.now,max_line:c.max};
  const cursor={now_move_id:c.selected};
  const result=stepJumpLifecycle(world,cursor,c.action);
  assert.equal(result.event,c.event);
  assert.deepEqual(result.effects,c.effects);
  assert.deepEqual(result.state,{display_jump:c.next_mode,key_flag:c.next_key,now_line:c.next_now,max_line:c.max});
  assert.equal(world.display_jump,c.mode);
  assert.equal(cursor.now_move_id,c.selected);
});
test('confirm cleanup stays locked; cancel cleanup unlocks',()=>{
  const world={display_jump:1,key_flag:0,now_line:4,max_line:10};
  const confirmed=stepJumpLifecycle(world,{now_move_id:7},'confirm');
  const cleaned=stepJumpLifecycle(confirmed.state,null,'cleanup');
  assert.equal(cleaned.state.now_line,7);
  assert.equal(cleaned.state.key_flag,0);
  assert.deepEqual(cleaned.effects,['del_movie:mt_line_jump','set_line_display:1']);
  const cancelled=stepJumpLifecycle({...world,display_jump:3},null,'cancel');
  const cancelCleaned=stepJumpLifecycle(cancelled.state,null,'cleanup');
  assert.equal(cancelCleaned.state.key_flag,1);
});
test('invalid states and cursor fail closed',()=>{
  const world={display_jump:1,key_flag:0,now_line:4,max_line:10};
  for(const selected of [0,21,true,null])
    assert.throws(()=>stepJumpLifecycle(world,{now_move_id:selected},'confirm'),/selected floor/);
  for(const [mode,action] of [[0,'confirm'],[2,'cancel'],[3,'cleanup'],[1,'cleanup']])
    assert.throws(()=>stepJumpLifecycle({...world,display_jump:mode},null,action));
  assert.throws(()=>stepJumpLifecycle({...world,max_line:true},null,'cancel'),/fields required/);
});
