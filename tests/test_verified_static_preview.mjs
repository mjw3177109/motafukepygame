import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {renderVerifiedStaticPreview} from '../web/verified_static_preview.mjs';

function fixture() {
  const files=[], shapes={}, verified={}, pins={}, blobs=new Map();
  for (const [alias,id] of [['mt_00',222],['mt_01',219]]) {
    const path=`shapes/${id}.svg`, bytes=new TextEncoder().encode(`<svg id="${id}"/>`);
    blobs.set(path,bytes);
    const sha256=createHash('sha256').update(bytes).digest('hex');
    files.push({path,sha256}); shapes[String(id)]={path,sha256};
    verified[alias]={shape_id:id,source:path,sha256,origin_x:15.95,origin_y:15.95};
    pins[alias]={shape_id:id,origin_x:15.95,origin_y:15.95};
  }
  const swf='a'.repeat(64), calls=[], decoded=[];
  return {
    report:{schema_version:1,swf_sha256:swf,
      registration_verified_for_static_aliases:true,
      verified_static_aliases:verified,shapes},
    anchors:{schema_version:1,swf_sha256:swf,aliases:pins},
    manifest:{original:{sha256:swf},files},
    plan:{floor_refresh_pending:true,key_unlock:false,placements:[
      {source:'mt_00',instance:'a',depth:8,x:48,y:64},
      {source:'mt_01',instance:'b',depth:2,x:16,y:32}]},
    readSvg:async path=>blobs.get(path),
    decodeSvg:async bytes=>{decoded.push(bytes);return {bytes};},
    ctx:{drawImage:(image,x,y)=>calls.push({image,x,y})},
    calls,decoded,blobs
  };
}
test('verified static images reach Canvas with original offsets and depth order',async()=>{
  const f=fixture();
  assert.equal(await renderVerifiedStaticPreview(f.ctx,f.plan,f),2);
  assert.deepEqual(f.calls.map(c=>new TextDecoder().decode(c.image.bytes)),
    ['<svg id="219"/>','<svg id="222"/>']);
  assert.ok(Math.abs(f.calls[0].x-0.05)<1e-10);
  assert.ok(Math.abs(f.calls[0].y-16.05)<1e-10);
  assert.ok(Math.abs(f.calls[1].x-32.05)<1e-10);
  assert.equal(f.plan.key_unlock,false);
  assert.equal(f.plan.floor_refresh_pending,true);
});
test('unverified animated alias fails before reads or drawing',async()=>{
  const f=fixture();f.plan.placements[0].source='mt_02';
  await assert.rejects(renderVerifiedStaticPreview(f.ctx,f.plan,f),/unverified\/animated alias/);
  assert.equal(f.decoded.length,0);assert.equal(f.calls.length,0);
});
test('tampered SVG blocks decoding and all draws',async()=>{
  const f=fixture();f.blobs.set('shapes/219.svg',new TextEncoder().encode('altered'));
  await assert.rejects(renderVerifiedStaticPreview(f.ctx,f.plan,f),/SHA256 mismatch/);
  assert.equal(f.decoded.length,0);assert.equal(f.calls.length,0);
});
test('invalid duplicate placement cannot partially render',async()=>{
  const f=fixture();f.plan.placements[1].instance='a';
  await assert.rejects(renderVerifiedStaticPreview(f.ctx,f.plan,f),/duplicate sprite placement/);
  assert.equal(f.calls.length,0);
});
test('unlocked plan rejected before decoding',async()=>{
  const f=fixture();f.plan.key_unlock=true;
  await assert.rejects(renderVerifiedStaticPreview(f.ctx,f.plan,f),/input-locked/);
  assert.equal(f.decoded.length,0);assert.equal(f.calls.length,0);
});
