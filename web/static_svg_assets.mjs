// Load source-verified static mt_00/mt_01 FFDec SVGs into Canvas assets.
const NAMES = ['mt_00','mt_01'], SHA = /^[0-9a-f]{64}$/;
const obj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const own = (x,k) => Object.prototype.hasOwnProperty.call(x,k);
async function readDefault(path) {
  const r=await fetch(path,{cache:'no-store'});
  if (!r.ok) throw new Error('SVG fetch failed');
  return new Uint8Array(await r.arrayBuffer());
}
async function decodeDefault(bytes) {
  return createImageBitmap(new Blob([bytes],{type:'image/svg+xml'}));
}
export async function loadVerifiedStaticAssets({report,anchors,manifest,
  readSvg=readDefault,decodeSvg=decodeDefault}) {
  if (![report,anchors,manifest,manifest?.original,anchors?.aliases,
      report?.verified_static_aliases,report?.shapes].every(obj) ||
      !Array.isArray(manifest.files) || anchors.schema_version!==1 ||
      report.schema_version!==1 || typeof anchors.swf_sha256!=='string' ||
      !SHA.test(anchors.swf_sha256) ||
      manifest.original.sha256!==anchors.swf_sha256 ||
      report.swf_sha256!==anchors.swf_sha256 ||
      report.registration_verified_for_static_aliases!==true ||
      Object.keys(anchors.aliases).length!==2 ||
      Object.keys(report.verified_static_aliases).length!==2 ||
      NAMES.some(n=>!own(anchors.aliases,n)||!own(report.verified_static_aliases,n))) {
    throw new Error('unverified static source or SWF provenance');
  }
  if (typeof readSvg!=='function' || typeof decodeSvg!=='function' ||
      !globalThis.crypto?.subtle?.digest) throw new Error('reader, decoder and SHA256 required');
  const inventory=new Map();
  for (const f of manifest.files) {
    if (!obj(f)||typeof f.path!=='string'||inventory.has(f.path))
      throw new Error('invalid/duplicate FFDec inventory');
    inventory.set(f.path,f.sha256);
  }
  const pending=[];
  for (const alias of NAMES) {
    const pin=anchors.aliases[alias], entry=report.verified_static_aliases[alias];
    if (!obj(pin)||!obj(entry)||!Number.isSafeInteger(pin.shape_id)||
        pin.shape_id<=0||!Number.isFinite(pin.origin_x)||!Number.isFinite(pin.origin_y))
      throw new Error('invalid source registration');
    const path=`shapes/${pin.shape_id}.svg`, shape=report.shapes[String(pin.shape_id)];
    if (entry.shape_id!==pin.shape_id||entry.source!==path||
        entry.origin_x!==pin.origin_x||entry.origin_y!==pin.origin_y||
        typeof entry.sha256!=='string'||!SHA.test(entry.sha256)||
        inventory.get(path)!==entry.sha256||!obj(shape)||
        shape.path!==path||shape.sha256!==entry.sha256)
      throw new Error(`unverified static metadata: ${alias}`);
    const raw=await readSvg(path);
    if (!(raw instanceof Uint8Array)) throw new Error('SVG reader must return Uint8Array');
    const bytes=new Uint8Array(raw);
    const digest=await globalThis.crypto.subtle.digest('SHA-256',bytes);
    const hex=[...new Uint8Array(digest)].map(n=>n.toString(16).padStart(2,'0')).join('');
    if (hex!==entry.sha256) throw new Error(`SVG SHA256 mismatch: ${alias}`);
    pending.push({alias,bytes,origin_x:pin.origin_x,origin_y:pin.origin_y});
  }
  const assets=Object.create(null);
  for (const p of pending) {
    const image=await decodeSvg(p.bytes);
    if (image==null) throw new Error(`decoder returned no image: ${p.alias}`);
    assets[p.alias]={image,origin_x:p.origin_x,origin_y:p.origin_y};
  }
  return assets;
}
