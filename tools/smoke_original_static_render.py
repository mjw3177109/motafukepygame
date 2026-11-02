"""Raster smoke test using *actual* FFDec SVGs, Pygame and CairoSVG.

This is a render/decode diagnostic, NOT Flash screenshot or gameplay parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

ALIASES = ('mt_00', 'mt_01')


def make_preview_plan(alias):
    """One isolated, source-verified sprite per transparent preview."""
    if alias not in ALIASES:
        raise ValueError('only two source-verified static aliases are allowed')
    return {
        'floor_refresh_pending': True,
        'key_unlock': False,
        'placements': [{'source': alias, 'instance': 'source-static-preview',
                        'depth': 1, 'x': 32, 'y': 32}],
    }


def validate_visible_result(blits, alpha_pixels, bounding_rect, width=64, height=64):
    """Fail closed on empty, clipped or missing source sprite renders."""
    if blits != 1 or type(alpha_pixels) is not int or alpha_pixels <= 0:
        raise ValueError('source sprite did not produce visible pixels')
    if (len(bounding_rect) != 4 or any(type(v) is not int for v in bounding_rect)):
        raise ValueError('invalid alpha bounding rectangle')
    x, y, w, h = bounding_rect
    if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > width or y + h > height:
        raise ValueError('source sprite alpha bounds exceed preview surface')


def run(manifest_path, report_path, anchors_path, export_root, out_dir):
    # Headless, but the actual pygame.Surface / pygame.image.load / blit path.
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    import pygame
    from core.verified_static_preview import render_verified_static_preview

    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    report = json.loads(Path(report_path).read_text(encoding='utf-8'))
    anchors = json.loads(Path(anchors_path).read_text(encoding='utf-8'))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    for alias in ALIASES:
        surface = pygame.Surface((64, 64), flags=pygame.SRCALPHA, depth=32)
        surface.fill((0, 0, 0, 0))
        blits = render_verified_static_preview(surface, make_preview_plan(alias),
            report, anchors, manifest, export_root)
        mask = pygame.mask.from_surface(surface, threshold=1)
        rects = mask.get_bounding_rects()
        if not rects:
            raise ValueError(f'empty source SVG rasterization: {alias}')
        left = min(r.left for r in rects)
        top = min(r.top for r in rects)
        right = max(r.right for r in rects)
        bottom = max(r.bottom for r in rects)
        bbox = [left, top, right - left, bottom - top]
        count = mask.count()
        validate_visible_result(blits, count, bbox)
        path = out / f'{alias}.png'
        pygame.image.save(surface, str(path))
        blob = path.read_bytes()
        if not blob.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError(f'not a PNG: {alias}')
        results[alias] = {
            'source_shape_id': anchors['aliases'][alias]['shape_id'],
            'source_svg_sha256': report['verified_static_aliases'][alias]['sha256'],
            'png': path.name,
            'png_sha256': hashlib.sha256(blob).hexdigest(),
            'alpha_pixels': count,
            'alpha_bounds_xywh': bbox,
            'canvas_wh': [64, 64],
        }
    result = {
        'schema_version': 1,
        'swf_sha256': anchors['swf_sha256'],
        'renderer': 'pygame + cairosvg',
        'original_svg_raster_smoke': 'passed',
        'flash_pixel_parity_verified': False,
        'html5_visual_parity_verified': False,
        'gameplay_parity_verified': False,
        'sprites': results,
    }
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS: two original FFDec SVGs rasterized through real Pygame; Flash/HTML5 parity NOT VERIFIED')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--anchors', type=Path, required=True)
    parser.add_argument('--export-root', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.report, args.anchors, args.export_root, args.out_dir)


if __name__ == '__main__':
    main()
