"""Isolated mt_06 source-hashed Pygame/Chromium smoke; NOT Flash parity or binding."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

ALIAS = 'mt_06'
SHAPE = 197
SOURCE = 'shapes/197.svg'


def verify_source(manifest, registration, anchors, export_root):
    """Fail closed before either renderer runs; never approve the runtime binding."""
    if not all(isinstance(x, dict) for x in (manifest, registration, anchors)):
        raise ValueError('missing original provenance')
    swf = anchors.get('swf_sha256')
    candidates = registration.get('static_registration_candidates')
    pins = anchors.get('candidate_aliases')
    if (anchors.get('schema_version') != 1 or registration.get('schema_version') != 1 or
        not isinstance(swf, str) or len(swf) != 64 or
        not isinstance(manifest.get('original'), dict) or manifest['original'].get('sha256') != swf or
        registration.get('swf_sha256') != swf or
        registration.get('registration_verified_for_static_aliases') is not True or
        registration.get('visual_parity_verified') is not False or
        registration.get('rasterization_verified') is not False or
        not isinstance(candidates, dict) or set(candidates) != {ALIAS} or
        not isinstance(pins, dict) or set(pins) != {ALIAS}):
        raise ValueError('mt_06 provenance or review gate mismatch')
    candidate, pin = candidates[ALIAS], pins[ALIAS]
    shape = registration.get('shapes', {}).get(str(SHAPE))
    if (not all(isinstance(x, dict) for x in (candidate, pin, shape)) or
        candidate.get('shape_id') != SHAPE or pin.get('shape_id') != SHAPE or
        candidate.get('source') != SOURCE or shape.get('path') != SOURCE or
        candidate.get('origin_x') != pin.get('origin_x') or
        candidate.get('origin_y') != pin.get('origin_y') or
        (pin.get('origin_x'), pin.get('origin_y')) != (16, 16) or
        shape.get('rect_twips') != [-320, 320, -320, 320] or
        candidate.get('ready_for_dual_renderer_smoke') is not True or
        candidate.get('flash_visual_parity_verified') is not False):
        raise ValueError('mt_06 shape, registration or candidate gate mismatch')
    digest = pin.get('source_sha256')
    if (not isinstance(digest, str) or len(digest) != 64 or
        candidate.get('sha256') != digest or shape.get('sha256') != digest):
        raise ValueError('mt_06 source hash anchor mismatch')
    files = manifest.get('files')
    if not isinstance(files, list) or any(not isinstance(f, dict) for f in files):
        raise ValueError('invalid FFDec manifest')
    entries = [f for f in files if f.get('path') == SOURCE]
    if len(entries) != 1 or entries[0].get('sha256') != digest:
        raise ValueError('mt_06 manifest source hash mismatch')
    root = Path(export_root).resolve()
    path = (root / SOURCE).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('unsafe or missing mt_06 SVG')
    from tools.audit_shape_registration import svg_size
    svg = path.read_bytes()
    if hashlib.sha256(svg).hexdigest() != digest or svg_size(svg) != (32, 32):
        raise ValueError('mt_06 SVG bytes or dimensions mismatch')
    return swf, digest, svg


def render_pygame(svg):
    """Use an actual 64x64 pygame.Surface, not a PIL approximation."""
    import cairosvg
    import pygame
    tile = pygame.image.load(io.BytesIO(cairosvg.svg2png(bytestring=svg)), 'mt_06.png')
    if tile.get_size() != (32, 32):
        raise ValueError('unexpected mt_06 tile dimensions')
    surface = pygame.Surface((64, 64), flags=pygame.SRCALPHA, depth=32)
    surface.fill((0, 0, 0, 0))
    surface.blit(tile, (16, 16))
    return pygame.image.tobytes(surface, 'RGBA')


def run(manifest_path, registration_path, anchors_path, export_root, out_dir, chromium_path=None):
    from PIL import Image
    from tools.experiment_svg_image_rendering import render_chromium
    from playwright.sync_api import sync_playwright
    load = lambda p: json.loads(Path(p).read_text(encoding='utf-8'))
    swf, digest, svg = verify_source(load(manifest_path), load(registration_path),
                                     load(anchors_path), export_root)
    pygame_rgba = render_pygame(svg)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=chromium_path)
        try:
            page = browser.new_page()
            page.goto('about:blank')
            chromium_rgba = render_chromium(page, svg, 16, 16)
            chromium_version = browser.version
        finally:
            browser.close()
    from tools.audit_dual_raster_pixels import compare_rgba, inspect_rgba
    pygame_alpha = inspect_rgba(pygame_rgba)
    chromium_alpha = inspect_rgba(chromium_rgba)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, rgba in (('pygame', pygame_rgba), ('chromium', chromium_rgba)):
        path = out / f'mt_06_{name}.png'
        Image.frombytes('RGBA', (64, 64), rgba).save(path)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = {'schema_version': 1, 'alias': ALIAS, 'shape_id': SHAPE,
              'swf_sha256': swf, 'source_svg_sha256': digest,
              'chromium_version': chromium_version,
              'pygame_png_sha256': hashes['pygame'], 'chromium_png_sha256': hashes['chromium'],
              'pygame_alpha': pygame_alpha, 'chromium_alpha': chromium_alpha,
              'pygame_vs_chromium': compare_rgba(pygame_rgba, chromium_rgba),
              'runtime_binding_approved': False, 'flash_visual_parity_verified': False,
              'gameplay_parity_verified': False, 'gymnasium_ready': False, 'kaggle_started': False}
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS: source-hashed mt_06 Pygame/Chromium diagnostic; Flash parity NOT VERIFIED')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('manifest', 'registration', 'anchors', 'export-root', 'out-dir'):
        parser.add_argument('--' + arg, type=Path, required=True)
    parser.add_argument('--chromium-path', default=None)
    a = parser.parse_args()
    run(a.manifest, a.registration, a.anchors, a.export_root, a.out_dir, a.chromium_path)


if __name__ == '__main__':
    main()
