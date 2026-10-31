"""Compare source-verified Pygame/Chromium PNG pixels without claiming Flash parity.

Requires real original FFDec smoke reports. Differences are diagnostic, never
silently treated as success or as evidence of original Flash pixel equivalence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ALIASES = ('mt_00', 'mt_01')
SIZE = (64, 64)


def inspect_rgba(rgba: bytes, width=64, height=64):
    if len(rgba) != width * height * 4:
        raise ValueError('invalid RGBA byte length')
    visible = []
    for i in range(width * height):
        if rgba[i * 4 + 3] > 1:
            visible.append((i % width, i // width))
    if not visible:
        raise ValueError('blank source raster')
    x0, x1 = min(x for x, _ in visible), max(x for x, _ in visible)
    y0, y1 = min(y for _, y in visible), max(y for _, y in visible)
    return {'alpha_pixels': len(visible),
            'alpha_bounds_xywh': [x0, y0, x1 - x0 + 1, y1 - y0 + 1]}


def compare_rgba(left: bytes, right: bytes, width=64, height=64):
    if len(left) != width * height * 4 or len(right) != len(left):
        raise ValueError('raster sizes differ or are not RGBA')
    changed = rgb = alpha = rgb_only = alpha_only = 0
    max_delta = [0, 0, 0, 0]
    total_delta = [0, 0, 0, 0]
    positions = []
    for i in range(width * height):
        off = i * 4
        delta = [abs(left[off + c] - right[off + c]) for c in range(4)]
        has_rgb, has_alpha = any(delta[:3]), bool(delta[3])
        if has_rgb or has_alpha:
            changed += 1
            positions.append((i % width, i // width))
        rgb += bool(has_rgb)
        alpha += has_alpha
        rgb_only += bool(has_rgb and not has_alpha)
        alpha_only += bool(has_alpha and not has_rgb)
        for c in range(4):
            max_delta[c] = max(max_delta[c], delta[c])
            total_delta[c] += delta[c]
    bbox = None
    if positions:
        x0, x1 = min(x for x, _ in positions), max(x for x, _ in positions)
        y0, y1 = min(y for _, y in positions), max(y for _, y in positions)
        bbox = [x0, y0, x1 - x0 + 1, y1 - y0 + 1]
    return {'canvas_pixels': width * height, 'different_rgba_pixels': changed,
            'different_rgb_pixels': rgb, 'different_alpha_pixels': alpha,
            'rgb_only_different_pixels': rgb_only, 'alpha_only_different_pixels': alpha_only,
            'max_abs_delta_rgba': max_delta,
            'mean_abs_delta_rgba': [round(v / (width * height), 6) for v in total_delta],
            'difference_bounds_xywh': bbox, 'exact_rgba_equal': changed == 0}


def verify_reports(pygame_report, browser_report):
    if not isinstance(pygame_report, dict) or not isinstance(browser_report, dict):
        raise ValueError('missing raster reports')
    swf = pygame_report.get('swf_sha256')
    if (not isinstance(swf, str) or not re.fullmatch(r'[0-9a-f]{64}', swf) or
            browser_report.get('swf_sha256') != swf or
            pygame_report.get('original_svg_raster_smoke') != 'passed' or
            browser_report.get('original_html5_svg_raster_smoke') != 'passed' or
            not isinstance(pygame_report.get('sprites'), dict) or
            not isinstance(browser_report.get('sprites'), dict) or
            set(pygame_report['sprites']) != set(ALIASES) or
            set(browser_report['sprites']) != set(ALIASES) or
            pygame_report.get('flash_pixel_parity_verified') is not False or
            browser_report.get('flash_pixel_parity_verified') is not False):
        raise ValueError('missing verified original raster provenance')
    for alias in ALIASES:
        p, b = pygame_report['sprites'][alias], browser_report['sprites'][alias]
        if (p.get('source_shape_id') != b.get('source_shape_id') or
                p.get('source_svg_sha256') != b.get('source_svg_sha256') or
                p.get('canvas_wh') != list(SIZE) or b.get('canvas_wh') != list(SIZE) or
                p.get('png') != f'{alias}.png' or b.get('png') != f'{alias}.png'):
            raise ValueError(f'original shape or raster metadata mismatch: {alias}')
    return swf


def read_verified_png(path, metadata):
    data = path.read_bytes()
    if (not data.startswith(b'\x89PNG\r\n\x1a\n') or
            hashlib.sha256(data).hexdigest() != metadata.get('png_sha256')):
        raise ValueError(f'PNG source hash/signature mismatch: {path.name}')
    import pygame
    surface = pygame.image.load(str(path))
    if surface.get_size() != SIZE:
        raise ValueError(f'wrong PNG dimensions: {path.name}')
    rgba = pygame.image.tobytes(surface, 'RGBA')
    actual = inspect_rgba(rgba, *SIZE)
    if any(actual[k] != metadata.get(k) for k in ('alpha_pixels', 'alpha_bounds_xywh')):
        raise ValueError(f'PNG alpha metadata mismatch: {path.name}')
    return rgba


def run(pygame_dir, browser_dir, out_path):
    pdir, bdir = Path(pygame_dir), Path(browser_dir)
    p = json.loads((pdir / 'report.json').read_text(encoding='utf-8'))
    b = json.loads((bdir / 'report.json').read_text(encoding='utf-8'))
    swf = verify_reports(p, b)
    results = {}
    for alias in ALIASES:
        left = read_verified_png(pdir / f'{alias}.png', p['sprites'][alias])
        right = read_verified_png(bdir / f'{alias}.png', b['sprites'][alias])
        results[alias] = {
            'shape_id': p['sprites'][alias]['source_shape_id'],
            'source_svg_sha256': p['sprites'][alias]['source_svg_sha256'],
            'pygame_png_sha256': p['sprites'][alias]['png_sha256'],
            'browser_png_sha256': b['sprites'][alias]['png_sha256'],
            **compare_rgba(left, right, *SIZE),
        }
    output = {'schema_version': 1, 'swf_sha256': swf,
              'comparison': 'Pygame/CairoSVG versus Chromium/Canvas; not Flash',
              'original_png_hashes_verified': True,
              'flash_pixel_parity_verified': False,
              'gameplay_parity_verified': False,
              'gymnasium_kaggle_started': False,
              'sprites': results}
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print('PASS: source-hashed dual-raster pixel differences recorded; Flash parity NOT VERIFIED')
    for alias in ALIASES:
        print(f"{alias}: {results[alias]['different_rgba_pixels']} / 4096 RGBA pixels differ; "
              f"{results[alias]['different_alpha_pixels']} alpha pixels differ")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pygame-dir', type=Path, required=True)
    parser.add_argument('--browser-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.pygame_dir, args.browser_dir, args.out)


if __name__ == '__main__':
    main()
