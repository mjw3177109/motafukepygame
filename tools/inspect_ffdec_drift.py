"""Read-only byte diagnostics for paths reported by independent FFDec exports.

This is evidence only; matching decompiled text does not verify ActionRecord
semantics, original gameplay, or Kaggle readiness.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def _safe_path(name):
    if not isinstance(name, str) or not name or '\\' in name or '\x00' in name:
        raise ValueError('invalid relative path')
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')):
        raise ValueError('unsafe relative path')
    return name


def _read(root, name):
    path = root / _safe_path(name)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        return None
    return path.read_bytes()


def summarize(report, first_root, second_root):
    result = []
    for category in ('changed', 'only_first', 'only_second'):
        entries = report.get(category, [])
        if not isinstance(entries, list):
            raise ValueError('invalid drift report category')
        for entry in entries:
            name = entry if isinstance(entry, str) else entry.get('path') if isinstance(entry, dict) else None
            _safe_path(name)
            first, second = _read(first_root, name), _read(second_root, name)
            # A reported difference without its expected evidence must not look like a valid summary.
            if (category == 'changed' and (first is None or second is None or first == second)) or \
               (category == 'only_first' and (first is None or second is not None)) or \
               (category == 'only_second' and (second is None or first is not None)):
                raise ValueError(f'incomplete or contradictory drift evidence: {category}: {name}')

            def info(data):
                return None if data is None else {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

            diff = next((i for i, (a, b) in enumerate(zip(first, second)) if a != b), None) if first is not None and second is not None else None
            if diff is None and first is not None and second is not None and len(first) != len(second):
                diff = min(len(first), len(second))
            result.append({'category': category, 'path': name, 'first': info(first), 'second': info(second),
                           'first_difference_offset': diff, 'actionrecord_semantics_verified': False})
    return {'schema_version': 1, 'drift': result, 'gameplay_parity_verified': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--first-root', type=Path, required=True)
    p.add_argument('--second-root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    result = summarize(json.loads(args.report.read_text(encoding='utf-8')), args.first_root, args.second_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
