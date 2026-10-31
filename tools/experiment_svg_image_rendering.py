"""Controlled image-rendering hint experiment on source-verified FFDec SVGs.

Renders isolated original SVGs through CairoSVG and Chromium without changing
production assets. The original variant must reproduce archived baseline PNGs.
This is a rasterizer diagnostic, NOT evidence of original Flash parity.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
from pathlib import Path

from tools.audit_svg_sampling import audit as audit_svg_sources
from tools.audit_dual_raster_pixels import compare_rgba, verify_reports

ALIASES = ('mt_00', 'mt_01')
VARIANTS = ('original', 'auto', 'pixelated', 'crisp-edges')


def make_variant(svg: bytes, variant: str) -> bytes:
    if variant not in VARIANTS:
        raise ValueError('unsupported image-rendering experiment variant')
    if variant == 'original':
        return svg
    # Source-verified FFDec SVGs have exactly one unhinted embedded <image>.
    # Restrict this experiment to that explicit syntax; never rewrite source files.
    if len(re.findall(rb'<image\s', svg)) != 1 or re.search(rb'<image\s[^>]*\bimage-rendering\s*=', svg):
        raise ValueError('unexpected source SVG image structure')
    return re.sub(rb'<image\s', f'<image image-rendering="{variant}" '.encode(), svg, count=1)


def pixel_counts(left: bytes, right: bytes) -> dict:
    if len(left) != 64 * 64 * 4 or len(right) != len(left):
        raise ValueError('expected two 64x64 RGBA rasters')
    result = compare_rgba(left, right)
    return {k: result[k] for k in ('different_rgba_pixels', 'different_rgb_pixels',
                                   'different_alpha_pixels', 'difference_bounds_xywh')}


def checked_baseline(path: Path, metadata: dict) -> bytes:
    from PIL import Image
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != metadata.get('png_sha256'):
        raise ValueError(f'archived baseline PNG SHA256 mismatch: {path.name}')
    with Image.open(io.BytesIO(data)) as image:
        if image.size != (64, 64):
            raise ValueError('archived baseline dimensions mismatch')
        return image.convert('RGBA').tobytes()


def render_cairo(svg: bytes) -> bytes:
    import cairosvg
    from PIL import Image
    with Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg))) as tile:
        if tile.size != (32, 32):
            raise ValueError('unexpected CairoSVG tile size')
        output = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        output.paste(tile.convert('RGBA'), (16, 16))
    return output.tobytes()


def render_chromium(page, svg: bytes, origin_x: float, origin_y: float) -> bytes:
    from PIL import Image
    encoded = page.evaluate('''async ({svg, x, y}) => {
      const canvas=document.createElement('canvas');canvas.width=canvas.height=64;
      const ctx=canvas.getContext('2d');
      const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));
      try {
        const img=new Image();img.src=url;await img.decode();
        ctx.drawImage(img,32-x,32-y);
        return canvas.toDataURL('image/png').split(',')[1];
      } finally {URL.revokeObjectURL(url);}
    }''', {'svg': svg.decode('utf-8'), 'x': origin_x, 'y': origin_y})
    with Image.open(io.BytesIO(base64.b64decode(encoded, validate=True))) as image:
        if image.size != (64, 64):
            raise ValueError('unexpected Chromium canvas size')
        return image.convert('RGBA').tobytes()


def run(manifest_path, registration_path, anchors_path, export_root,
        pygame_dir, browser_dir, out_path, chromium_path=None):
    from playwright.sync_api import sync_playwright
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    registration = json.loads(Path(registration_path).read_text(encoding='utf-8'))
    anchors = json.loads(Path(anchors_path).read_text(encoding='utf-8'))
    source_audit = audit_svg_sources(manifest, registration, export_root)
    p = json.loads((Path(pygame_dir) / 'report.json').read_text(encoding='utf-8'))
    b = json.loads((Path(browser_dir) / 'report.json').read_text(encoding='utf-8'))
    swf = verify_reports(p, b, registration, anchors)
    if source_audit['swf_sha256'] != swf:
        raise ValueError('source audit and archived raster SWF mismatch')
    output = {'schema_version': 1, 'swf_sha256': swf,
              'experiment': 'isolated SVG image-rendering hints; no production changes',
              'flash_pixel_parity_verified': False, 'sampling_root_cause_verified': False,
              'gymnasium_kaggle_started': False, 'sprites': {}}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=chromium_path)
        try:
            page = browser.new_page()
            page.goto('about:blank')
            output['chromium_version'] = browser.version
            for alias in ALIASES:
                source = source_audit['sprites'][alias]
                shape = source['shape_id']
                original = (Path(export_root) / f'shapes/{shape}.svg').read_bytes()
                if hashlib.sha256(original).hexdigest() != source['svg_sha256']:
                    raise ValueError(f'original SVG hash drift: {alias}')
                if (source['image_count'] != 1 or source['pattern_count'] != 1 or
                        source['images'][0]['media_type'] != 'image/png' or
                        source['images'][0]['image_rendering'] is not None):
                    raise ValueError(f'unsupported source image/pattern count: {alias}')
                pin = anchors['aliases'][alias]
                original_p = checked_baseline(Path(pygame_dir) / f'{alias}.png', p['sprites'][alias])
                original_b = checked_baseline(Path(browser_dir) / f'{alias}.png', b['sprites'][alias])
                variants = {}
                baseline_p = baseline_b = None
                for variant in VARIANTS:
                    candidate = make_variant(original, variant)
                    cairo = render_cairo(candidate)
                    chrome = render_chromium(page, candidate, pin['origin_x'], pin['origin_y'])
                    if variant == 'original':
                        if cairo != original_p or chrome != original_b:
                            raise ValueError(f'experiment baseline does not reproduce archived renders: {alias}')
                        baseline_p, baseline_b = cairo, chrome
                    variants[variant] = {
                        'candidate_svg_sha256': hashlib.sha256(candidate).hexdigest(),
                        'cairo_delta_from_original': pixel_counts(baseline_p, cairo),
                        'chromium_delta_from_original': pixel_counts(baseline_b, chrome),
                        'cairo_vs_chromium': pixel_counts(cairo, chrome),
                    }
                output['sprites'][alias] = {'shape_id': shape,
                    'original_svg_sha256': source['svg_sha256'],
                    'archived_baselines_reproduced': True, 'variants': variants}
        finally:
            browser.close()
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    for alias, item in output['sprites'].items():
        print(alias, {variant: data['cairo_vs_chromium']['different_rgba_pixels']
                      for variant, data in item['variants'].items()})
    print('PASS: source-hashed controlled rasterizer experiment; Flash parity NOT VERIFIED')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'registration', 'anchors', 'export-root', 'pygame-dir',
                 'browser-dir', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--chromium-path', default=None)
    args = parser.parse_args()
    run(args.manifest, args.registration, args.anchors, args.export_root,
        args.pygame_dir, args.browser_dir, args.out, args.chromium_path)


if __name__ == '__main__':
    main()
