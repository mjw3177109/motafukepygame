"""Audit independently captured Flash mt_06 stage crops; never grant parity."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path

from tools.verify_mt06_artifacts import verify

SIZE = (64, 64)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _read_image(path: Path, expected_sha: str):
    from PIL import Image
    if not _valid_sha(expected_sha) or not path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') or _sha256(path) != expected_sha:
        raise ValueError(f'Flash capture PNG hash mismatch: {path.name}')
    with Image.open(path) as img:
        img.load()
        if img.mode not in ('RGB', 'RGBA'):
            raise ValueError(f'Flash capture must be RGB/RGBA: {path.name}')
        return img.copy().convert('RGB')


def _utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith('Z'):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0


def _rgb_differences(left, right) -> int:
    if left.size != right.size:
        raise ValueError('Flash crop / renderer dimensions mismatch')
    a, b = left.tobytes(), right.tobytes()
    return sum(a[i:i + 3] != b[i:i + 3] for i in range(0, len(a), 3))


def audit(report: dict, anchors: dict, png_dir: Path, baseline_dir: Path | None) -> dict:
    """Verify existing renderer evidence, then optional independent Flash capture."""
    from PIL import Image

    verified = verify(report, anchors, png_dir)
    output = {
        'schema_version': 1,
        'alias': 'mt_06',
        'swf_sha256': verified['swf_sha256'],
        'source_svg_sha256': verified['source_svg_sha256'],
        'renderer_artifacts_verified': True,
        'flash_capture_status': 'missing',
        'original_flash_reference_available': False,
        'flash_visual_parity_verified': False,
        'runtime_binding_approved': False,
        'gameplay_parity_verified': False,
        'gymnasium_ready': False,
        'kaggle_started': False,
    }
    if baseline_dir is None or not Path(baseline_dir).exists():
        return output

    baseline_dir = Path(baseline_dir)
    metadata_path = baseline_dir / 'capture.json'
    if not metadata_path.is_file():
        raise ValueError('Flash capture directory exists but capture.json is missing')
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    if not isinstance(metadata, dict):
        raise ValueError('Flash capture metadata must be an object')
    for key in ('player_name', 'player_version', 'capture_method', 'scene_id'):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f'Flash capture missing provenance field: {key}')
    for key in ('flash_visual_parity_verified', 'runtime_binding_approved', 'gymnasium_ready', 'kaggle_started'):
        if metadata.get(key, False) is not False:
            raise ValueError(f'Flash capture cannot preapprove gate: {key}')
    rect = metadata.get('crop_rect')
    bg = metadata.get('background_rgb')
    frame = metadata.get('frame_index')
    if (metadata.get('schema_version') != 1 or metadata.get('alias') != 'mt_06' or
        metadata.get('swf_sha256') != verified['swf_sha256'] or
        metadata.get('source_svg_sha256') != verified['source_svg_sha256'] or
        not _utc_timestamp(metadata.get('capture_utc')) or
        type(frame) is not int or frame < 0 or
        not isinstance(rect, list) or len(rect) != 4 or
        any(type(n) is not int for n in rect) or rect[0] < 0 or rect[1] < 0 or
        rect[2:] != [64, 64] or
        not isinstance(bg, list) or len(bg) != 3 or
        any(type(n) is not int or not 0 <= n <= 255 for n in bg)):
        raise ValueError('Flash capture provenance / crop / frame metadata mismatch')

    stage = _read_image(baseline_dir / 'original_stage.png', metadata.get('original_stage_sha256'))
    crop = _read_image(baseline_dir / 'reference_crop.png', metadata.get('reference_crop_sha256'))
    x, y, w, h = rect
    if x + w > stage.width or y + h > stage.height or crop.size != SIZE:
        raise ValueError('Flash capture crop outside original stage or wrong size')
    if stage.crop((x, y, x + w, y + h)).tobytes() != crop.tobytes():
        raise ValueError('Flash reference crop is not an exact raw-stage crop')

    def composite_renderer(name: str):
        with Image.open(Path(png_dir) / f'mt_06_{name}.png') as image:
            image.load()
            backdrop = Image.new('RGBA', SIZE, tuple(bg) + (255,))
            backdrop.alpha_composite(image.convert('RGBA'))
            return backdrop.convert('RGB')

    output.update({
        'flash_capture_status': 'captured_unreviewed',
        'original_flash_reference_available': True,
        'capture_utc': metadata['capture_utc'],
        'player_name': metadata['player_name'],
        'player_version': metadata['player_version'],
        'frame_index': frame,
        'original_stage_sha256': metadata['original_stage_sha256'],
        'reference_crop_sha256': metadata['reference_crop_sha256'],
        'pygame_vs_flash_rgb_different_pixels': _rgb_differences(composite_renderer('pygame'), crop),
        'chromium_vs_flash_rgb_different_pixels': _rgb_differences(composite_renderer('chromium'), crop),
        'comparison_limit': 'raw stage crop vs solid-background composite; player authenticity and human alignment not approved',
    })
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--anchors', type=Path, required=True)
    parser.add_argument('--png-dir', type=Path, required=True)
    parser.add_argument('--baseline-dir', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(json.loads(args.report.read_text(encoding='utf-8')),
                   json.loads(args.anchors.read_text(encoding='utf-8')),
                   args.png_dir, args.baseline_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"PASS: mt_06 Flash baseline {result['flash_capture_status']}; Flash parity NOT VERIFIED")


if __name__ == '__main__':
    main()
