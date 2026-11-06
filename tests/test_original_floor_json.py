"""Regression for numeric-token and duplicate-key safety before floor planning."""
import unittest
from core.original_floor_json import load_original_floor_json


class OriginalFloorJsonTests(unittest.TestCase):
    def test_canonical_integers_preserve_values(self):
        self.assertEqual(load_original_floor_json('{"floors":{"0":[[99,98,-1]]}}'),
                         {'floors': {'0': [[99, 98, -1]]}})

    def test_fractional_and_exponent_tokens_fail_closed(self):
        for token in ('99.0', '9.9e1', '1e2', '-0.0'):
            with self.subTest(token=token), self.assertRaises(ValueError):
                load_original_floor_json('{"floors":{"0":[[' + token + ']]}}')

    def test_unsafe_integer_and_nonfinite_fail_closed(self):
        for token in ('9007199254740992', '-9007199254740992', 'NaN', 'Infinity'):
            with self.subTest(token=token), self.assertRaises(ValueError):
                load_original_floor_json('[' + token + ']')

    def test_invalid_json_rejected(self):
        with self.assertRaises(ValueError):
            load_original_floor_json('{"floors":')

    def test_duplicate_floor_and_nested_keys_rejected(self):
        for source in ('{"floors":{"00":[],"00":[]}}',
                       '{"floors":{"00":[[99]]},"floors":{}}',
                       '{"source":{"sha":"a","sha":"b"}}'):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'duplicate JSON object key'):
                load_original_floor_json(source)


if __name__ == '__main__':
    unittest.main()
