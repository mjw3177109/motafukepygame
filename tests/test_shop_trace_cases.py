"""Tests for source-only shop transition vectors; not runtime parity."""
import copy
import json
import unittest
from pathlib import Path
from tools.shop_trace_cases import build_cases

FIXTURE = Path(__file__).resolve().parents[1] / 'data/original_shop_transactions_static.json'


class ShopTraceCasesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))

    def test_twenty_purchase_and_exit_vectors(self):
        cases = build_cases(self.fixture)
        self.assertEqual(len(cases), 20)
        self.assertEqual(sum(c['success'] for c in cases), 14)
        self.assertEqual(len({(c['frame'], c['option'], c['before']['gold']) for c in cases}), 20)
        for case in cases:
            with self.subTest(frame=case['frame'], option=case['option'], gold=case['before']['gold']):
                if case['option'] == 4:
                    self.assertEqual(case['before'], case['after'])
                    self.assertEqual(case['before']['gold'], 0)
                    self.assertEqual(case['exit_action'], {2: 'gotoAndPlay', 4: 'gotoAndStop'}[case['frame']])
                    self.assertEqual(case['exit_label'], 'end')
                    continue
                row = next(r for r in self.fixture['transactions']
                           if (r['frame'], r['option']) == (case['frame'], case['option']))
                before, after = case['before'], case['after']
                self.assertEqual(case['provenance'], 'static_actionscript_expectation_not_runtime')
                self.assertEqual(after['gold'], before['gold'] - (row['cost'] if case['success'] else 0))
                for field in ('hp', 'attack', 'defense', 'yellow_key', 'blue_key', 'red_key'):
                    expected = before[field] + (row['delta'].get(field, 0) if case['success'] else 0)
                    self.assertEqual(after[field], expected)

    def test_runtime_gate_cannot_be_marked_passed(self):
        for gate in self.fixture['gates']:
            fixture = copy.deepcopy(self.fixture)
            fixture['gates'][gate] = True
            with self.subTest(gate=gate), self.assertRaises(ValueError):
                build_cases(fixture)

    def test_falsey_non_boolean_gates_rejected(self):
        # A falsey placeholder is not an audited boolean False.
        for invalid in (0, None, '', [], {}):
            for gate in self.fixture['gates']:
                fixture = copy.deepcopy(self.fixture)
                fixture['gates'][gate] = invalid
                with self.subTest(gate=gate, invalid=invalid), self.assertRaises(ValueError):
                    build_cases(fixture)

    def test_malformed_fixture_root_and_missing_transactions_fail_closed(self):
        for invalid in (None, [], 'invalid', 0):
            with self.subTest(root=invalid), self.assertRaises(ValueError):
                build_cases(invalid)
        fixture = copy.deepcopy(self.fixture)
        del fixture['transactions']
        with self.assertRaises(ValueError):
            build_cases(fixture)

    def test_malformed_transaction_fields_fail_closed(self):
        for field, invalid in (('cost', None), ('cost', True),
                               ('delta', None), ('delta', [])):
            fixture = copy.deepcopy(self.fixture)
            fixture['transactions'][0][field] = invalid
            with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                build_cases(fixture)
        for missing in ('cost', 'delta'):
            fixture = copy.deepcopy(self.fixture)
            del fixture['transactions'][0][missing]
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                build_cases(fixture)

    def test_boolean_stat_delta_rejected(self):
        # JSON booleans are Python ints; never accept true as a +1 stat gain.
        for invalid in (True, False):
            fixture = copy.deepcopy(self.fixture)
            fixture['transactions'][0]['delta']['hp'] = invalid
            with self.subTest(delta=invalid), self.assertRaises(ValueError):
                build_cases(fixture)

    def test_invalid_purchase_slots_rejected(self):
        # Six unique entries alone do not prove that they match the source frames.
        for frame, option in ((3, 1), (2, 4), (True, 1), (2, False)):
            fixture = copy.deepcopy(self.fixture)
            fixture['transactions'][0]['frame'] = frame
            fixture['transactions'][0]['option'] = option
            with self.subTest(frame=frame, option=option), self.assertRaises(ValueError):
                build_cases(fixture)

    def test_source_backed_price_and_effect_cannot_drift(self):
        for field, bad_value in (('cost', 26), ('delta', {'attack': 800})):
            fixture = copy.deepcopy(self.fixture)
            fixture['transactions'][0][field] = bad_value
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_cases(fixture)

    def test_source_backed_key_effect_cannot_be_swapped(self):
        fixture = copy.deepcopy(self.fixture)
        fixture['transactions'][3]['delta'] = {'blue_key': 1}
        with self.assertRaises(ValueError):
            build_cases(fixture)

    def test_invalid_exit_slots_rejected(self):
        # Python considers bool an int; neither is a valid Flash frame/option slot.
        for field, invalid in (('frame', True), ('option', True),
                               ('frame', '2'), ('option', '4')):
            fixture = copy.deepcopy(self.fixture)
            fixture['exit'][0][field] = invalid
            with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):
                build_cases(fixture)

    def test_malformed_exit_entries_rejected(self):
        for invalid in (None, 'invalid', 2):
            fixture = copy.deepcopy(self.fixture)
            fixture['exit'][0] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                build_cases(fixture)

    def test_fixture_not_mutated(self):
        before = copy.deepcopy(self.fixture)
        build_cases(self.fixture)
        self.assertEqual(self.fixture, before)


if __name__ == '__main__':
    unittest.main()
