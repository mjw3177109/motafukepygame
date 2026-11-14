// Original-SWF-verified two-sprite Canvas preview, never a floor-complete signal.
import {loadVerifiedStaticAssets} from './static_svg_assets.mjs';
import {drawFloorPlan} from './floor_render.mjs';

const ALIASES = new Set(['mt_00','mt_01']);

export async function renderVerifiedStaticPreview(ctx, plan, {
  report, anchors, manifest, readSvg, decodeSvg
}) {
  if (!plan || plan.floor_refresh_pending !== true ||
      plan.key_unlock !== false || !Array.isArray(plan.placements) ||
      plan.placements.length === 0) {
    throw new Error('preview requires a pending input-locked floor plan');
  }
  for (const p of plan.placements) {
    if (!p || !ALIASES.has(p.source)) {
      throw new Error('preview cannot render unverified/animated alias');
    }
  }
  const assets = await loadVerifiedStaticAssets({report,anchors,manifest,
                                                  readSvg,decodeSvg});
  return drawFloorPlan(ctx,plan,assets);
}
