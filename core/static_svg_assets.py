"""Load only source-verified static FFDec SVGs into Pygame floor asset mappings.

No raster/pixel parity, animation, floor completion or keyboard unlock claim.
"""
import hashlib
import io
import math
import re
from pathlib import Path

ALIASES = {'mt_00', 'mt_01'}
SHA = re.compile(r'[0-9a-f]{64}\Z')


def decode_pygame_svg(data):
    """Optional CairoSVG/Pygame rasterizer; import dependencies only when used."""
    import cairosvg
    import pygame
    return pygame.image.load(io.BytesIO(cairosvg.svg2png(bytestring=data)), 'static.png')


def load_verified_static_assets(report, anchors, manifest, export_root, decoder=None):
    """Check all original hashes before decoding; return floor_render-compatible assets."""
    if not all(isinstance(v, dict) for v in (report, anchors, manifest)):
        raise ValueError('missing source metadata')
    swf = anchors.get('swf_sha256')
    original, pins = manifest.get('original'), anchors.get('aliases')
    verified, shapes, files = report.get('verified_static_aliases'), report.get('shapes'), manifest.get('files')
    if (not isinstance(original, dict) or not isinstance(pins, dict) or
        not isinstance(verified, dict) or not isinstance(shapes, dict) or not isinstance(files, list) or
        anchors.get('schema_version') != 1 or report.get('schema_version') != 1 or
        not isinstance(swf, str) or not SHA.fullmatch(swf) or
        original.get('sha256') != swf or report.get('swf_sha256') != swf or
        report.get('registration_verified_for_static_aliases') is not True or
        set(pins) != ALIASES or set(verified) != ALIASES):
        raise ValueError('unverified static source or SWF provenance')
    inventory = {}
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get('path'), str) or item['path'] in inventory:
            raise ValueError('invalid/duplicate FFDec inventory')
        inventory[item['path']] = item.get('sha256')
    root = Path(export_root).resolve()
    pending = []
    for alias in sorted(ALIASES):
        pin, entry = pins[alias], verified[alias]
        if not isinstance(pin, dict) or not isinstance(entry, dict):
            raise ValueError('invalid static alias')
        cid = pin.get('shape_id')
        if (type(cid) is not int or cid <= 0 or
            any(type(pin.get(k)) not in (int, float) or not math.isfinite(pin[k])
                for k in ('origin_x', 'origin_y'))):
            raise ValueError('invalid source registration')
        rel = f'shapes/{cid}.svg'
        digest = entry.get('sha256')
        shape = shapes.get(str(cid))
        if (entry.get('shape_id') != cid or entry.get('source') != rel or
            any(entry.get(k) != pin[k] for k in ('origin_x', 'origin_y')) or
            not isinstance(digest, str) or not SHA.fullmatch(digest) or
            inventory.get(rel) != digest or not isinstance(shape, dict) or
            shape.get('path') != rel or shape.get('sha256') != digest):
            raise ValueError(f'unverified static metadata: {alias}')
        path = (root / rel).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f'unsafe/missing SVG: {alias}')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f'SVG SHA256 mismatch: {alias}')
        pending.append((alias, data, pin['origin_x'], pin['origin_y']))
    decoder = decode_pygame_svg if decoder is None else decoder
    if not callable(decoder):
        raise ValueError('decoder must be callable')
    assets = {}
    for alias, data, ox, oy in pending:
        image = decoder(data)
        if image is None:
            raise ValueError(f'decoder returned no image: {alias}')
        assets[alias] = {'image': image, 'origin_x': ox, 'origin_y': oy}
    return assets
