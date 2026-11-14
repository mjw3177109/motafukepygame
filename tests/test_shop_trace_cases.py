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

    def test_eighteen_boundary_vectors(self):
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

    def test_fixture_not_mutated(self):
        before = copy.deepcopy(self.fixture)
        build_cases(self.fixture)
        self.assertEqual(self.fixture, before)


if __name__ == '__main__':
    unittest.main()
