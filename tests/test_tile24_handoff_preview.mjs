import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {previewTile24Handoff} from '../web/tile24_handoff_preview.mjs';

const cases=JSON.parse(readFileSync(new URL('./fixtures/tile24_state_cases.json',import.meta.url),'utf8'));
function world(tile=24,blocked=false) {
  const grid=Array.from({length:11},()=>Array(11).fill(0));grid[5][6]=tile;
  return {grid,row:5,col:5,keys:{yellow:0,blue:0,red:0},
    key_flag:blocked?0:1,display_list:0,display_jump:0,
    display_text:0,display_buy:0,display_kill:0};
}
test('tile-24 router handoff connects to review-only commands without mutations',()=>{
  const w=world(),review=structuredClone(cases.find(c=>c.name==='three_independent_guards').input);
  const before=structuredClone(w),beforeReview=structuredClone(review);
  const result=previewTile24Handoff(w,2,{},review);
  assert.deepEqual(result.target,[5,6]);
  assert.equal(result.event,'tile24_review_only');
  assert.deepEqual(result.review.trace.map(x=>x.branch),
    ['initial_dialogue','ending_state_change','floor22_dialogue']);
  assert.equal(result.review.trace.filter(x=>x.clip_command).length,2);
  assert.equal(result.review.source_branch_order_verified,false);
  for (const field of ['state_mapping_verified','flash_runtime_verified','executable','gymnasium_ready'])
    assert.equal(result[field],false);
  assert.deepEqual(w,before);assert.deepEqual(review,beforeReview);
});
test('blocked, non-event and malformed review input fail closed',()=>{
  const review=structuredClone(cases[1].input);
  for (const w of [world(24,true),world(0)]) {
    const before=structuredClone(w);
    assert.throws(()=>previewTile24Handoff(w,2,{},review),/no tile-24 handoff/);
    assert.deepEqual(w,before);
  }
  const w=world(),before=structuredClone(w);
  for (const bad of [{...review,tile_id:129},{...review,get_money:[1,1]}])
    assert.throws(()=>previewTile24Handoff(w,2,{},bad));
  assert.deepEqual(w,before);
});

test('inherited tile_id cannot authorize a tile-24 review handoff',()=>{
  const w=world();
  const review=structuredClone(cases.find(c=>c.name==='three_independent_guards').input);
  const inherited=Object.assign(Object.create({tile_id:24}),review);
  delete inherited.tile_id;
  const before=structuredClone(w);
  assert.throws(()=>previewTile24Handoff(w,2,{},inherited),
    /explicit tile-24 review state required/);
  assert.deepEqual(w,before);
});
