"""Fail-closed FFDec ActionScript provenance check with one isolated diagnostic retry.

An intermittent FFDec export must never be treated as a verified original.
The retry is evidence collection only; it does not replace the first export,
update source anchors, or unlock gameplay / Kaggle parity gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

SCRIPT_PREFIX = 'export/scripts/'
EXPORT_TYPES = 'script,image,shape,sound,text,button,font,binaryData'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_renderer_path(name: object) -> str:
    if not isinstance(name, str) or not name.startswith(SCRIPT_PREFIX) or '\\' in name or '\x00' in name:
        raise ValueError('invalid renderer ActionScript path')
    if any(segment in ('', '.', '..') for segment in name.split('/')):
        raise ValueError('unsafe renderer ActionScript path')
    if PurePosixPath(name).is_absolute() or not name.endswith('.as'):
        raise ValueError('invalid renderer ActionScript path')
    return name


def byte_summary(data: bytes | None) -> dict | None:
    if data is None:
        return None
    return {'sha256': sha256(data), 'size': len(data),
            'crlf': data.count(b'\r\n'), 'lf': data.count(b'\n'),
            'nul': data.count(b'\x00')}


def first_difference(left: bytes, right: bytes) -> int | None:
    for i, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return i
    return min(len(left), len(right)) if len(left) != len(right) else None


def classify(expected: str, first: bytes | None, repeated: bytes | None) -> str:
    if first is not None and sha256(first) == expected:
        return 'first_export_matches_anchor'
    if repeated is None:
        return 'mismatch_repeat_unavailable'
    if sha256(repeated) == expected:
        return 'repeat_matches_anchor_first_does_not'
    if first is not None and first == repeated:
        return 'repeatable_mismatch_against_anchor'
    return 'two_distinct_mismatches_against_anchor'


def _read_export(root: Path, relative: str) -> bytes | None:
    path = root / relative
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        return None
    return path.read_bytes()


def diagnose(committed: dict, manifest: dict, swf: Path, ffdec: Path,
             export_root: Path, timeout: int = 180) -> dict:
    if not isinstance(committed, dict) or not isinstance(manifest, dict):
        raise ValueError('committed source and FFDec manifest must be JSON objects')
    source = committed.get('source')
    if not isinstance(source, dict):
        raise ValueError('missing committed original source anchors')
    relative = safe_renderer_path(source.get('renderer_actionscript_path'))
    expected = source.get('renderer_actionscript_sha256')
    swf_expected = source.get('swf_sha256')
    if not all(isinstance(x, str) and len(x) == 64 and all(c in '0123456789abcdef' for c in x)
               for x in (expected, swf_expected)):
        raise ValueError('invalid anchored SHA256')
    if not swf.is_file() or not ffdec.is_file():
        raise ValueError('original SWF or FFDec jar missing')
    swf_actual = sha256(swf.read_bytes())
    original = manifest.get('original')
    if not isinstance(original, dict):
        raise ValueError('FFDec manifest original metadata must be an object')
    if swf_actual != swf_expected or original.get('sha256') != swf_expected:
        raise ValueError('SWF provenance mismatch; diagnostic retry forbidden')
    entries = manifest.get('files')
    if not isinstance(entries, list):
        raise ValueError('missing export manifest')
    found = [e for e in entries if isinstance(e, dict) and e.get('path') == relative.removeprefix('export/')]
    if len(found) != 1:
        raise ValueError('renderer script missing or duplicated in manifest')
    first = _read_export(export_root, relative.removeprefix('export/'))
    initial = byte_summary(first)
    result = {'schema_version': 1, 'swf_sha256': swf_actual,
              'ffdec_jar_sha256': sha256(ffdec.read_bytes()),
              'renderer_script': relative, 'expected_sha256': expected,
              'manifest_sha256': found[0].get('sha256'), 'first': initial,
              'repeat': None, 'repeat_exit_code': None, 'repeat_log': None,
              'first_vs_repeat_first_difference': None,
              'classification': None, 'provenance_verified': False,
              'gameplay_parity_verified': False, 'kaggle_started': False}
    if first is not None and sha256(first) == expected:
        if found[0].get('sha256') != expected:
            # The exported bytes are correct, but the manifest is inconsistent.
            # Retrying FFDec cannot repair this independent provenance failure.
            result['classification'] = 'manifest_hash_mismatch_first_export_matches_anchor'
            return result
        result['classification'] = 'first_export_matches_anchor'
        result['provenance_verified'] = True
        return result
    # On mismatch only: independently re-export with the same FFDec arguments.
    # This retry is never copied into the original export directory.
    with tempfile.TemporaryDirectory(prefix='mota-ffdec-repeat-') as tmp:
        target = Path(tmp) / 'export'
        command = ['java', '-Xmx2g', '-Djava.awt.headless=true', '-jar', str(ffdec),
                   '-cli', '-onerror', 'ignore', '-export', EXPORT_TYPES,
                   str(target), str(swf)]
        try:
            completed = subprocess.run(command, text=True, capture_output=True,
                                       timeout=timeout, check=False)
            result['repeat_exit_code'] = completed.returncode
            result['repeat_log'] = (completed.stdout + '\n' + completed.stderr)[-12000:]
        except (OSError, subprocess.TimeoutExpired) as exc:
            result['repeat_log'] = f'{type(exc).__name__}: {exc}'[-12000:]
        repeated = _read_export(target, relative.removeprefix('export/'))
        result['repeat'] = byte_summary(repeated)
        if first is not None and repeated is not None:
            result['first_vs_repeat_first_difference'] = first_difference(first, repeated)
        result['classification'] = classify(expected, first, repeated)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--committed', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--swf', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--export-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = diagnose(json.loads(args.committed.read_text(encoding='utf-8')),
                          json.loads(args.manifest.read_text(encoding='utf-8')),
                          args.swf, args.ffdec, args.export_root)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        # A failed provenance check must still leave an inspectable CI artifact.
        # This is diagnostic evidence, never a successful provenance verdict.
        unavailable = {
            'schema_version': 1,
            'classification': 'diagnostic_unavailable',
            'error_type': type(exc).__name__,
            'error_message': str(exc)[:500],
            'provenance_verified': False,
            'gameplay_parity_verified': False,
            'kaggle_started': False,
        }
        try:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(unavailable, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        except OSError:
            # Never convert a report-write failure into a pass.
            pass
        parser.exit(2, f'FAIL: FFDec script drift diagnosis unavailable: {exc}\n')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    if not result['provenance_verified']:
        parser.exit(2, f"FAIL: original FFDec renderer script mismatch; {result['classification']}; see {args.out}\n")
    print('PASS: renderer script bytes match independent source anchor; gameplay parity NOT VERIFIED')


if __name__ == '__main__':
    main()
