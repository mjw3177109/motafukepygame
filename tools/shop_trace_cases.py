"""Generate deterministic shop transition vectors from the *static* SWF fixture.

These are reference expectations, not Flash runtime recordings or parity evidence.
"""
import argparse
import json
from pathlib import Path

DEFAULT_FIXTURE = Path(__file__).resolve().parents[1] / 'data/original_shop_transactions_static.json'
BASE = {'hp': 10, 'attack': 3, 'defense': 2, 'yellow_key': 0, 'blue_key': 0, 'red_key': 0}


def build_cases(fixture):
    if fixture.get('verification') != 'static_actionscript_only_not_runtime_parity':
        raise ValueError('Refusing fixture without static-only provenance')
    if any(fixture.get('gates', {}).values()) or set(fixture.get('gates', {})) != {
        'actionrecord_verified', 'flash_runtime_verified', 'pygame_verified', 'html5_verified'
    }:
        raise ValueError('Unexpected verification gates')
    rows = fixture['transactions']
    expected_slots = {(frame, option) for frame in (2, 4) for option in (1, 2, 3)}
    if (not isinstance(rows, list) or len(rows) != 6
            or any(type(r.get('frame')) is not int or type(r.get('option')) is not int
                   for r in rows if isinstance(r, dict))
            or any(not isinstance(r, dict) for r in rows)
            or {(r['frame'], r['option']) for r in rows} != expected_slots):
        raise ValueError('Expected six source-backed frame/option slots')
    # Lock each source-backed slot to its observed price and stat effect.
    # Slot uniqueness alone would permit a silently swapped shop effect.
    expected_transactions = {
        (2, 1): (25, {'hp': 800}),
        (2, 2): (25, {'attack': 4}),
        (2, 3): (25, {'defense': 4}),
        (4, 1): (10, {'yellow_key': 1}),
        (4, 2): (50, {'blue_key': 1}),
        (4, 3): (100, {'red_key': 1}),
    }
    if any((row['cost'], row['delta']) != expected_transactions[(row['frame'], row['option'])]
           for row in rows):
        raise ValueError('Shop transaction differs from source-backed slot')
    cases = []
    for row in sorted(rows, key=lambda r: (r['frame'], r['option'])):
        cost = row['cost']
        if not isinstance(cost, int) or isinstance(cost, bool) or cost <= 0:
            raise ValueError('Invalid price')
        if len(row['delta']) != 1 or any(k not in BASE or type(v) is not int or v <= 0 for k, v in row['delta'].items()):
            raise ValueError('Invalid stat delta')
        for balance in (cost - 1, cost, cost + 1):
            before = {'gold': balance, **BASE}
            after = dict(before)
            success = balance >= cost
            if success:
                after['gold'] -= cost
                for key, value in row['delta'].items():
                    after[key] += value
            cases.append({'provenance': 'static_actionscript_expectation_not_runtime',
                          'frame': row['frame'], 'option': row['option'],
                          'before': before, 'after': after, 'success': success})
    exits = fixture.get('exit', [])
    if (not isinstance(exits, list) or len(exits) != 2
            or any(not isinstance(e, dict) or type(e.get('frame')) is not int
                   or type(e.get('option')) is not int for e in exits)
            or {e['frame'] for e in exits} != {2, 4}):
        raise ValueError('Expected both source-backed exit actions')
    expected_actions = {2: 'gotoAndPlay', 4: 'gotoAndStop'}
    for row in sorted(exits, key=lambda e: e['frame']):
        if (row.get('option') != 4 or row.get('condition') != 'always'
                or row.get('label') != 'end'
                or row.get('action') != expected_actions[row['frame']]):
            raise ValueError('Unexpected source-backed exit instruction')
        state = {'gold': 0, **BASE}
        cases.append({'provenance': 'static_actionscript_expectation_not_runtime',
                      'frame': row['frame'], 'option': 4,
                      'before': dict(state), 'after': dict(state),
                      'success': True, 'exit_action': row['action'],
                      'exit_label': 'end'})
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding='utf-8'))
    cases = build_cases(fixture)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(''.join(json.dumps(c, sort_keys=True, ensure_ascii=False) + '\n' for c in cases), encoding='utf-8')
    print(f'Wrote {len(cases)} static-only vectors to {args.out}')


if __name__ == '__main__':
    main()
