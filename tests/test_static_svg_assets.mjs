import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {loadVerifiedStaticAssets} from '../web/static_svg_assets.mjs';
function fixture() {
  const blobs=new Map(), files=[], shapes={}, aliases={}, pins={};
  for (const [name,id] of [['mt_00',222],['mt_01',219]]) {
    const path=`shapes/${id}.svg`, bytes=new TextEncoder().encode(`<svg id="${id}"/>`);
    blobs.set(path,bytes);
    const sha256=createHash('sha256').update(bytes).digest('hex');
    files.push({path,sha256}); shapes[String(id)]={path,sha256};
    aliases[name]={shape_id:id,source:path,sha256,origin_x:15.95,origin_y:15.95};
    pins[name]={shape_id:id,origin_x:15.95,origin_y:15.95};
  }
  const report={schema_version:1,swf_sha256:'a'.repeat(64),
    registration_verified_for_static_aliases:true,verified_static_aliases:aliases,shapes};
  const anchors={schema_version:1,swf_sha256:'a'.repeat(64),aliases:pins};
  const manifest={original:{sha256:'a'.repeat(64)},files};
  const calls=[],readSvg=async path=>blobs.get(path);
  const decodeSvg=async bytes=>{calls.push(bytes);return {bytes};};
  return {report,anchors,manifest,readSvg,decodeSvg,blobs,calls};
}
test('two verified Canvas images and original offsets',async()=>{
  const f=fixture(),a=await loadVerifiedStaticAssets(f);
  assert.deepEqual(Object.keys(a),['mt_00','mt_01']);
  assert.equal(a.mt_00.origin_x,15.95);
  assert.deepEqual(a.mt_01.image.bytes,f.blobs.get('shapes/219.svg'));
});
test('tamper is rejected before decoding either image',async()=>{
  const f=fixture();f.blobs.set('shapes/219.svg',new TextEncoder().encode('bad'));
  await assert.rejects(loadVerifiedStaticAssets(f),/SHA256 mismatch/);
  assert.equal(f.calls.length,0);
});
test('SWF and registration drift are rejected',async()=>{
  const f=fixture();f.manifest.original.sha256='b'.repeat(64);
  await assert.rejects(loadVerifiedStaticAssets(f),/SWF provenance/);
  const g=fixture();g.report.verified_static_aliases.mt_00.origin_x=16;
  await assert.rejects(loadVerifiedStaticAssets(g),/unverified static metadata/);
});
test('unsupported alias and duplicate manifest rejected',async()=>{
  const f=fixture();f.report.verified_static_aliases.mt_02={};
  await assert.rejects(loadVerifiedStaticAssets(f),/unverified static source/);
  const g=fixture();g.manifest.files.push({...g.manifest.files[0]});
  await assert.rejects(loadVerifiedStaticAssets(g),/duplicate FFDec/);
});
test('missing bytes and empty image rejected',async()=>{
  const f=fixture();f.blobs.delete('shapes/222.svg');
  await assert.rejects(loadVerifiedStaticAssets(f),/Uint8Array/);
  const g=fixture();g.decodeSvg=async()=>null;
  await assert.rejects(loadVerifiedStaticAssets(g),/returned no image/);
});

import {decodeBrowserSvg} from '../web/static_svg_assets.mjs';

test('Blob SVG fast path does not allocate object URL',async()=>{
  const expected={bitmap:true};
  const image=await decodeBrowserSvg(new TextEncoder().encode('<svg/>'),{
    createBitmap:async()=>expected,
    createUrl:()=>{throw Error('unexpected fallback');}
  });
  assert.equal(image,expected);
});
test('Chromium SVG pattern decode fallback uses decoded Image and releases URL',async()=>{
  const calls=[],image={decode:async()=>{calls.push('decoded');}};
  const result=await decodeBrowserSvg(new TextEncoder().encode('<svg/>'),{
    createBitmap:async()=>{throw Error('InvalidStateError: SVG pattern');},
    createImage:()=>image,
    createUrl:blob=>{assert.equal(blob.type,'image/svg+xml');return 'blob:source-svg';},
    revokeUrl:url=>calls.push('revoke:'+url)
  });
  assert.equal(result,image);
  assert.equal(image.src,'blob:source-svg');
  assert.deepEqual(calls,['decoded','revoke:blob:source-svg']);
});
test('fallback decode failure still revokes object URL and fails closed',async()=>{
  const calls=[];
  await assert.rejects(decodeBrowserSvg(new Uint8Array([1,2]),{
    createBitmap:async()=>{throw Error('unsupported');},
    createImage:()=>({decode:async()=>{throw Error('bad SVG');}}),
    createUrl:()=> 'blob:bad',
    revokeUrl:url=>calls.push(url)
  }),/bad SVG/);
  assert.deepEqual(calls,['blob:bad']);
});
