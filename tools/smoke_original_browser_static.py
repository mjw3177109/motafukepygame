"""Render source-hashed FFDec mt_00/mt_01 SVGs in real Chromium Canvas.

This tests original SVG decode, placement and raster bounds, NOT Flash parity.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ALIASES = ('mt_00', 'mt_01')
MODULES = ('web/verified_static_preview.mjs', 'web/static_svg_assets.mjs',
           'web/floor_render.mjs')
ROOT = Path(__file__).resolve().parents[1]


def preview_plan(alias):
    if alias not in ALIASES:
        raise ValueError('only source-verified static aliases supported')
    return {'floor_refresh_pending': True, 'key_unlock': False,
            'placements': [{'source': alias, 'instance': 'original-static-preview',
                            'depth': 1, 'x': 32, 'y': 32}]}


def validate_browser_result(result, pygame_sprite, tolerance=2):
    if not isinstance(result, dict) or result.get('draws') != 1 or result.get('canvas_wh') != [64, 64]:
        raise ValueError('browser did not draw one 64x64 preview')
    count, box = result.get('alpha_pixels'), result.get('alpha_bounds_xywh')
    expected = pygame_sprite.get('alpha_bounds_xywh') if isinstance(pygame_sprite, dict) else None
    if type(count) is not int or count <= 0 or not isinstance(box, list) or len(box) != 4 or not all(type(v) is int for v in box):
        raise ValueError('browser alpha output invalid or empty')
    x, y, w, h = box
    if min(x, y) < 0 or min(w, h) <= 0 or x + w > 64 or y + h > 64:
        raise ValueError('browser preview clipped or out of bounds')
    if not isinstance(expected, list) or len(expected) != 4 or not all(type(v) is int for v in expected):
        raise ValueError('missing Pygame alpha reference')
    if type(tolerance) is not int or tolerance < 0 or any(abs(a - b) > tolerance for a, b in zip(box, expected)):
        raise ValueError('Chromium/Pygame registration bounds differ')
    return [abs(a - b) for a, b in zip(box, expected)]


def run(manifest_path, report_path, anchors_path, pygame_path, export_root, out_dir, chromium_path=None):
    from playwright.sync_api import sync_playwright  # CI-only dependency
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    report = json.loads(Path(report_path).read_text(encoding='utf-8'))
    anchors = json.loads(Path(anchors_path).read_text(encoding='utf-8'))
    pygame = json.loads(Path(pygame_path).read_text(encoding='utf-8'))
    swf = anchors.get('swf_sha256')
    if (manifest.get('original', {}).get('sha256') != swf or report.get('swf_sha256') != swf or
        pygame.get('swf_sha256') != swf or pygame.get('original_svg_raster_smoke') != 'passed'):
        raise ValueError('missing original SWF/Pygame provenance')
    shape_paths = {}
    for alias in ALIASES:
        pin = anchors['aliases'][alias]
        source = report['verified_static_aliases'][alias]
        prior = pygame['sprites'][alias]
        shape = pin['shape_id']
        if (type(shape) is not int or source['shape_id'] != shape or
            prior['source_shape_id'] != shape or prior['source_svg_sha256'] != source['sha256']):
            raise ValueError('original source shape mismatch')
        shape_paths[f'/shapes/{shape}.svg'] = Path(export_root) / 'shapes' / f'{shape}.svg'

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                content = b'<!doctype html><meta charset="utf-8"><canvas id="preview" width="64" height="64"></canvas>'
                mime = 'text/html; charset=utf-8'
            elif self.path.lstrip('/') in MODULES:
                content = (ROOT / self.path.lstrip('/')).read_bytes()
                mime = 'text/javascript; charset=utf-8'
            elif self.path in shape_paths:
                content = shape_paths[self.path].read_bytes()
                mime = 'image/svg+xml'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, *_args):
            pass

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path=chromium_path)
            try:
                page = browser.new_page(viewport={'width': 128, 'height': 128}, device_scale_factor=1)
                page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
                results = {}
                for alias in ALIASES:
                    result = page.evaluate("""async ({plan,report,anchors,manifest}) => {
                      const {renderVerifiedStaticPreview} = await import('/web/verified_static_preview.mjs');
                      const canvas=document.getElementById('preview'),ctx=canvas.getContext('2d');
                      ctx.clearRect(0,0,64,64);
                      const readSvg=async path=>{const response=await fetch('/'+path,{cache:'no-store'});
                        if(!response.ok)throw new Error('original SVG unavailable');
                        return new Uint8Array(await response.arrayBuffer());};
                      const draws=await renderVerifiedStaticPreview(ctx,plan,{report,anchors,manifest,readSvg});
                      const data=ctx.getImageData(0,0,64,64).data;
                      let count=0,left=64,top=64,right=-1,bottom=-1;
                      for(let y=0;y<64;y++)for(let x=0;x<64;x++){
                        if(data[(y*64+x)*4+3]>1){count++;left=Math.min(left,x);top=Math.min(top,y);
                          right=Math.max(right,x);bottom=Math.max(bottom,y);}}
                      return {draws,canvas_wh:[64,64],alpha_pixels:count,
                        alpha_bounds_xywh:count?[left,top,right-left+1,bottom-top+1]:null,
                        png_data_url:canvas.toDataURL('image/png')};
                    }""", {'plan': preview_plan(alias), 'report': report,
                           'anchors': anchors, 'manifest': manifest})
                    delta = validate_browser_result(result, pygame['sprites'][alias])
                    png_url = result.pop('png_data_url')
                    if not png_url.startswith('data:image/png;base64,'):
                        raise ValueError('browser did not produce PNG')
                    png = base64.b64decode(png_url.split(',', 1)[1], validate=True)
                    if not png.startswith(b'\x89PNG\r\n\x1a\n'):
                        raise ValueError('invalid browser PNG')
                    filename = f'{alias}.png'
                    (out / filename).write_bytes(png)
                    results[alias] = {**result, 'source_shape_id': anchors['aliases'][alias]['shape_id'],
                                      'source_svg_sha256': report['verified_static_aliases'][alias]['sha256'],
                                      'png': filename, 'png_sha256': hashlib.sha256(png).hexdigest(),
                                      'bounds_delta_from_pygame_xywh': delta}
                final = {'schema_version': 1, 'swf_sha256': swf,
                         'renderer': f'Chromium {browser.version} Canvas/createImageBitmap',
                         'original_html5_svg_raster_smoke': 'passed',
                         'pygame_html5_alpha_bounds_within_2px': True,
                         'flash_pixel_parity_verified': False, 'gameplay_parity_verified': False,
                         'sprites': results}
                (out / 'report.json').write_text(json.dumps(final, indent=2) + '\n', encoding='utf-8')
                print('PASS: original FFDec mt_00/mt_01 in Chromium Canvas; Pygame bounds <=2px; Flash parity NOT VERIFIED')
                return final
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('manifest', 'report', 'anchors', 'pygame', 'export-root', 'out-dir'):
        parser.add_argument('--' + arg, type=Path, required=True)
    parser.add_argument('--chromium-path', default=None)
    a = parser.parse_args()
    run(a.manifest, a.report, a.anchors, a.pygame, a.export_root, a.out_dir, a.chromium_path)


if __name__ == '__main__':
    main()
