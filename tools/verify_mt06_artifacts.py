"""Fail-closed audit of saved mt_06 Pygame/Chromium PNG evidence; NOT Flash parity.

The producer computes its report in memory. This consumer independently reopens
both archived PNGs and checks their byte hashes, alpha metrics, and RGBA diff.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.audit_dual_raster_pixels import compare_rgba, inspect_rgba

SIZE = (64, 64)
ALIAS = 'mt_06'
SHAPE_ID = 197


def _read_png(path: Path, expected_sha: str) -> bytes:
    from PIL import Image

    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise ValueError(f'missing PNG SHA256 for {path.name}')
    data = path.read_bytes()
    if not data.startswith(b'\x89PNG\r\n\x1a\n') or hashlib.sha256(data).hexdigest() != expected_sha:
        raise ValueError(f'PNG bytes/hash mismatch: {path.name}')
    with Image.open(path) as image:
        image.load()
        if image.size != SIZE or image.mode != 'RGBA':
            raise ValueError(f'PNG canvas/mode mismatch: {path.name}')
        return image.tobytes()


def verify(report: dict, anchors: dict, png_dir: Path) -> dict:
    """Verify saved artifacts against independent source pins; never grant parity."""
    if not isinstance(report, dict) or not isinstance(anchors, dict):
        raise ValueError('invalid report or source anchors')
    pinned = anchors.get('candidate_aliases')
    pin = pinned.get(ALIAS) if isinstance(pinned, dict) else None
    if (anchors.get('schema_version') != 1 or not isinstance(pin, dict) or
        pin.get('shape_id') != SHAPE_ID or
        (pin.get('origin_x'), pin.get('origin_y')) != (16, 16) or
        report.get('schema_version') != 1 or report.get('alias') != ALIAS or
        report.get('shape_id') != SHAPE_ID or
        report.get('swf_sha256') != anchors.get('swf_sha256') or
        report.get('source_svg_sha256') != pin.get('source_sha256') or
        not isinstance(report.get('chromium_version'), str) or
        not report['chromium_version'].strip()):
        raise ValueError('mt_06 report/source provenance mismatch')
    for key in ('runtime_binding_approved', 'flash_visual_parity_verified',
                'gameplay_parity_verified', 'gymnasium_ready', 'kaggle_started'):
        if report.get(key) is not False:
            raise ValueError(f'unsafe or missing acceptance gate: {key}')
    png_dir = Path(png_dir)
    left = _read_png(png_dir / 'mt_06_pygame.png', report.get('pygame_png_sha256'))
    right = _read_png(png_dir / 'mt_06_chromium.png', report.get('chromium_png_sha256'))
    if inspect_rgba(left, *SIZE) != report.get('pygame_alpha'):
        raise ValueError('saved Pygame alpha report mismatch')
    if inspect_rgba(right, *SIZE) != report.get('chromium_alpha'):
        raise ValueError('saved Chromium alpha report mismatch')
    measured = compare_rgba(left, right, *SIZE)
    if measured != report.get('pygame_vs_chromium'):
        raise ValueError('saved PNG RGBA comparison/report mismatch')
    return {
        'schema_version': 1,
        'alias': ALIAS,
        'swf_sha256': report['swf_sha256'],
        'source_svg_sha256': report['source_svg_sha256'],
        'archived_png_hashes_verified': True,
        'archived_png_alpha_verified': True,
        'archived_png_rgba_diff_verified': True,
        'different_rgba_pixels': measured['different_rgba_pixels'],
        'flash_visual_parity_verified': False,
        'runtime_binding_approved': False,
        'gymnasium_ready': False,
        'kaggle_started': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--anchors', required=True, type=Path)
    parser.add_argument('--png-dir', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    result = verify(json.loads(args.report.read_text(encoding='utf-8')),
                    json.loads(args.anchors.read_text(encoding='utf-8')), args.png_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS: archived mt_06 PNG bytes, alpha, RGBA diff independently verified; Flash parity NOT VERIFIED')


if __name__ == '__main__':
    main()
