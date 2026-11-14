// HTML5 Canvas draw adapter. Does not claim Flash pixel parity or unlock input.
export function prepareFloorDraws(plan, assets) {
  if (!plan || plan.floor_refresh_pending !== true || plan.key_unlock !== false ||
      !Array.isArray(plan.placements) || plan.placements.length === 0 ||
      !assets || typeof assets !== 'object') {
    throw new Error('requires a pending, input-locked floor placement plan and assets');
  }
  const seen = new Set();
  const prepared = plan.placements.map((p, index) => {
    if (!p || typeof p.source !== 'string' || !p.source ||
        typeof p.instance !== 'string' || !p.instance || seen.has(p.instance) ||
        !Number.isSafeInteger(p.depth) || !Number.isFinite(p.x) || !Number.isFinite(p.y)) {
      throw new Error('invalid or duplicate sprite placement');
    }
    seen.add(p.instance);
    const asset = Object.hasOwn(assets, p.source) ? assets[p.source] : undefined;
    if (!asset || asset.image == null || !Number.isFinite(asset.origin_x) ||
        !Number.isFinite(asset.origin_y)) {
      throw new Error(`missing verified image/registration for ${p.source}`);
    }
    return {source:p.source, instance:p.instance, depth:p.depth,
            x:p.x-asset.origin_x, y:p.y-asset.origin_y, image:asset.image, index};
  });
  prepared.sort((a,b) => a.depth-b.depth || a.index-b.index);
  return prepared.map(({index, ...draw}) => draw);
}

export function drawFloorPlan(ctx, plan, assets) {
  const draws = prepareFloorDraws(plan, assets);
  if (!ctx || typeof ctx.drawImage !== 'function') {
    throw new Error('ctx must provide drawImage(image, x, y)');
  }
  for (const item of draws) ctx.drawImage(item.image, item.x, item.y);
  return draws.length;
}
