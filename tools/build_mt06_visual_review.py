"""Build a source-checked, *two-renderer* mt_06 review sheet, not Flash proof.

Only Pygame and Chromium PNGs are available. A separate, independently
captured Flash reference is required before any original-visual parity claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tools.verify_mt06_artifacts import verify

SIZE = (64, 64)
SCALE = 4


def build(report: dict, anchors: dict, png_dir: Path, out_dir: Path) -> dict:
    """Validate archived inputs first; then produce human-readable diff evidence."""
    from PIL import Image, ImageDraw

    verified = verify(report, anchors, png_dir)
    png_dir, out_dir = Path(png_dir), Path(out_dir)
    with Image.open(png_dir / 'mt_06_pygame.png') as image:
        left = image.copy()
    with Image.open(png_dir / 'mt_06_chromium.png') as image:
        right = image.copy()

    mask = Image.new('RGBA', SIZE, (0, 0, 0, 255))
    changed = alpha_changed = 0
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            a, b = left.getpixel((x, y)), right.getpixel((x, y))
            if a != b:
                changed += 1
                if a[3] != b[3]:
                    alpha_changed += 1
                    mask.putpixel((x, y), (230, 50, 210, 255))
                else:
                    mask.putpixel((x, y), (235, 55, 45, 255))
    if (changed != verified['different_rgba_pixels'] or
            alpha_changed != report['pygame_vs_chromium']['different_alpha_pixels']):
        raise ValueError('review mask disagrees with verified PNG report')

    def checkerboard():
        canvas = Image.new('RGBA', SIZE, (235, 235, 235, 255))
        draw = ImageDraw.Draw(canvas)
        for y in range(0, SIZE[1], 8):
            for x in range(0, SIZE[0], 8):
                if ((x // 8) + (y // 8)) % 2:
                    draw.rectangle((x, y, x + 7, y + 7), fill=(195, 195, 195, 255))
        return canvas

    panes = []
    for image in (left, right):
        background = checkerboard()
        background.alpha_composite(image)
        panes.append(background.resize((SIZE[0] * SCALE, SIZE[1] * SCALE), Image.Resampling.NEAREST))
    panes.append(mask.resize((SIZE[0] * SCALE, SIZE[1] * SCALE), Image.Resampling.NEAREST))

    margin, header, gap = 12, 48, 12
    width = 2 * margin + 3 * SIZE[0] * SCALE + 2 * gap
    height = 2 * margin + header + SIZE[1] * SCALE + 34
    sheet = Image.new('RGB', (width, height), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, margin), 'mt_06 | two-renderer review only | NOT original Flash', fill=(20, 20, 20))
    labels = ('Pygame / CairoSVG', 'Chromium / Canvas', 'RGBA diff (red=RGB, magenta=alpha)')
    for i, (pane, label) in enumerate(zip(panes, labels)):
        x = margin + i * (SIZE[0] * SCALE + gap)
        draw.text((x, margin + 24), label, fill=(30, 30, 30))
        sheet.paste(pane.convert('RGB'), (x, margin + header))
    draw.text((margin, height - 24),
              f'{changed} RGBA differences; {alpha_changed} alpha differences; Flash baseline MISSING',
              fill=(30, 30, 30))

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / 'visual_review.png'
    sheet.save(path)
    output = {
        'schema_version': 1,
        'alias': 'mt_06',
        'swf_sha256': verified['swf_sha256'],
        'source_svg_sha256': verified['source_svg_sha256'],
        'pygame_png_sha256': report['pygame_png_sha256'],
        'chromium_png_sha256': report['chromium_png_sha256'],
        'visual_review_png_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'different_rgba_pixels': changed,
        'different_alpha_pixels': alpha_changed,
        'comparison': 'Pygame vs Chromium only; original Flash not sampled',
        'original_flash_reference_available': False,
        'flash_visual_parity_verified': False,
        'runtime_binding_approved': False,
        'gymnasium_ready': False,
        'kaggle_started': False,
    }
    (out_dir / 'visual_review.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--anchors', type=Path, required=True)
    parser.add_argument('--png-dir', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    result = build(json.loads(args.report.read_text(encoding='utf-8')),
                   json.loads(args.anchors.read_text(encoding='utf-8')),
                   args.png_dir, args.out_dir)
    print(f"PASS: mt_06 visual review sheet: {result['different_rgba_pixels']} RGBA differences; Flash NOT VERIFIED")


if __name__ == '__main__':
    main()
