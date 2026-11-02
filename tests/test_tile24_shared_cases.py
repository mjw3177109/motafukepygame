"""Shared synthetic tile-24 fixtures for Python and JS review probes, NOT Flash parity."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from test_audit_tile24_branch_order import SOURCE
from tools.trace_tile24_states import trace_tile24_states

CASES = json.loads((Path(__file__).parent / 'fixtures' / 'tile24_state_cases.json').read_text(encoding='utf-8'))


class Tile24SharedCasesTests(unittest.TestCase):
    def test_shared_synthetic_cases(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                original = deepcopy(case['input'])
                result = trace_tile24_states(original, SOURCE)
                self.assertEqual(original, case['input'])
                self.assertEqual([x['branch'] for x in result['trace']], case['branches'])
                self.assertEqual([x['dialogue_command'] for x in result['trace'] if 'dialogue_command' in x], case['dialogues'])
                self.assertEqual(result['state'], {**case['input'], **case['changed']})
                self.assertTrue(result['source_branch_order_verified'])
                self.assertFalse(result['flash_runtime_verified'])
                self.assertFalse(result['dual_client_parity_verified'])
                self.assertFalse(result['gymnasium_ready'])


if __name__ == '__main__':
    unittest.main()
