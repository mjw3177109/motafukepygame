"""Read-only diagnostics for FFDec's map ActionScript export; never grants parity."""
import argparse
import hashlib
import json
import re
from pathlib import Path

DECL = re.compile(r'(?m)^\s*mt_line_(\d{2})\s*=\s*new Array\((\d+)\);\s*$')

def inspect(data: bytes, expected_sha256: str) -> dict:
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256):
        raise ValueError('invalid source anchor')
    source = data.decode('utf-8-sig')
    found = [(int(f), int(n)) for f, n in DECL.findall(source)]
    present = {f for f, n in found if n == 11}
    duplicates = sorted({f for f, n in found if found.count((f, n)) > 1})
    digest = hashlib.sha256(data).hexdigest()
    return {'schema_version': 1, 'script_sha256': digest, 'expected_sha256': expected_sha256,
            'bytes': len(data), 'declarations': found, 'missing_floors': sorted(set(range(27)) - present),
            'duplicate_floors': duplicates, 'anchor_matches': digest == expected_sha256,
            'provenance_verified': False, 'gameplay_parity_verified': False, 'kaggle_started': False}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--script', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    result = inspect(args.script.read_bytes(), args.expected_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if not result['anchor_matches'] or result['missing_floors'] or result['duplicate_floors']:
        p.exit(2, 'FAIL: map ActionScript incomplete or differs from source anchor\n')
    print('PASS: map declaration diagnostics only; no parity approval')

if __name__ == '__main__':
    main()
