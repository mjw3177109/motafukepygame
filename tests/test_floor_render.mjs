import {test} from 'node:test';
import assert from 'node:assert/strict';
import {planJumpFloorTiles} from '../web/floor_tile_plan.mjs';
import {drawFloorPlan, prepareFloorDraws} from '../web/floor_render.mjs';

function fixture() {
  const m = Array.from({length:11},()=>Array(11).fill(0));
  m[0].splice(0,4,97,1,98,24);
  const plan = planJumpFloorTiles(m);
  const assets = Object.fromEntries([...new Set(plan.placements.map(p=>p.source))]
    .map(source=>[source,{image:{source},origin_x:4,origin_y:7}]));
  const calls = [];
  const ctx = {drawImage:(...args)=>calls.push(args)};
  return {plan,assets,ctx,calls};
}

test('Canvas draws sorted sprites with explicit registration offsets',()=>{
  const {plan,assets,ctx,calls}=fixture();
  const before=structuredClone(plan);
  assert.equal(drawFloorPlan(ctx,plan,assets),3);
  assert.deepEqual(calls.map(c=>c[0].source),['mt_01','mt_24','mt_99']);
  assert.deepEqual(calls[0].slice(1),[235,40]);
  assert.deepEqual(calls[2].slice(1),[203,40]);
  assert.deepEqual(plan,before);
  assert.equal(plan.key_unlock,false);
});
test('missing sprite fails before any draw',()=>{
  const {plan,assets,ctx,calls}=fixture();
  delete assets.mt_99;
  assert.throws(()=>drawFloorPlan(ctx,plan,assets),/missing verified/);
  assert.equal(calls.length,0);
});
test('missing registration fails before any draw',()=>{
  const {plan,assets,ctx,calls}=fixture();
  delete assets.mt_24.origin_x;
  assert.throws(()=>drawFloorPlan(ctx,plan,assets),/missing verified/);
  assert.equal(calls.length,0);
});
test('unlocked plan and duplicate instances fail closed',()=>{
  const {plan,assets}=fixture();
  assert.throws(()=>prepareFloorDraws({...plan,key_unlock:true},assets));
  assert.throws(()=>prepareFloorDraws({...plan,placements:[...plan.placements,plan.placements[0]]},assets));
});
test('invalid canvas context is rejected',()=>{
  const {plan,assets}=fixture();
  assert.throws(()=>drawFloorPlan(null,plan,assets));
});
