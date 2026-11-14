"""Source-verified two-sprite preview handoff, not a complete Flash floor.

Only mt_00/mt_01 are eligible. The original floor remains input-locked;
this function never marks refresh complete or modifies gameplay state.
"""

from core.floor_render import blit_floor_plan
from core.static_svg_assets import ALIASES, load_verified_static_assets


def render_verified_static_preview(surface, plan, report, anchors, manifest,
                                   export_root, decoder=None):
    """Load verified original SVGs, then blit a static-only placement plan.

    All aliases are checked before loading any bytes; the loader verifies all
    SVG hashes before decoding. The floor adapter preflights all placements
    before touching the target surface.
    """
    if (not isinstance(plan, dict) or
            plan.get('floor_refresh_pending') is not True or
            plan.get('key_unlock') is not False or
            not isinstance(plan.get('placements'), list) or
            not plan['placements']):
        raise ValueError('preview requires a pending input-locked floor plan')
    for placement in plan['placements']:
        if not isinstance(placement, dict) or placement.get('source') not in ALIASES:
            raise ValueError('preview cannot render unverified/animated alias')
    assets = load_verified_static_assets(report, anchors, manifest, export_root,
                                         decoder=decoder)
    return blit_floor_plan(surface, plan, assets)
