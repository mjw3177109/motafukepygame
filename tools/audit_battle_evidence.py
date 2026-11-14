"""Audit screenshot existence, SHA256, and PNG decodability for verified battle observations.

This does not establish that a screenshot came from the original Flash runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from tools.validate_flash_battle_trace import validate


def audit(trace_path, evidence_root):
    errors = validate(trace_path)
    if errors:
        return errors
    root = Path(evidence_root).resolve()
    for number, line in enumerate(Path(trace_path).read_text(encoding='utf-8').splitlines(), 1):
        row = json.loads(line)
        if not row['verified']:
            continue
        relative = Path(row['evidence_frame'])
        if relative.is_absolute() or '..' in relative.parts:
            errors.append(f'line {number}: unsafe evidence path')
            continue
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            errors.append(f'line {number}: missing or escaped evidence file')
            continue
        expected = row.get('evidence_sha256')
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
            errors.append(f'line {number}: missing or invalid evidence_sha256')
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != expected:
            errors.append(f'line {number}: evidence SHA256 mismatch')
            continue
        try:
            with Image.open(target) as frame:
                if frame.format != 'PNG':
                    errors.append(f'line {number}: evidence is not PNG')
                    continue
                frame.verify()
            with Image.open(target) as frame:
                frame.load()
        except (OSError, ValueError, UnidentifiedImageError):
            errors.append(f'line {number}: invalid or truncated PNG evidence')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--evidence-root', type=Path, required=True)
    args = parser.parse_args()
    errors = audit(args.trace, args.evidence_root)
    for error in errors:
        print('FAIL:', error)
    if errors:
        raise SystemExit(1)
    print('PASS: evidence hashes and PNG decode validated; Flash provenance NOT VERIFIED')


if __name__ == '__main__':
    main()
