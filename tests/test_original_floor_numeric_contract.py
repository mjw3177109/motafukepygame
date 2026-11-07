"""Regression fixtures for JSON numeric-token parity at the Python/JS boundary.

JSON.parse collapses 99.0 to Number 99, while Python json.loads keeps float.
A strict map loader must reject fractional/exponent notation before planning.
These are contract fixtures, not Flash runtime parity evidence.
"""
import json
import unittest

MAX_SAFE = 2**53 - 1


def reject_fraction(token):
    raise ValueError(f'non-integer JSON numeric token: {token}')


class OriginalFloorNumericContractTests(unittest.TestCase):
    def test_fractional_or_exponent_tokens_are_rejected(self):
        for token in ('99.0', '9.9e1', '1e2'):
            with self.subTest(token=token), self.assertRaises(ValueError):
                json.loads('{"floors":{"0":[[' + token + ']]}}', parse_float=reject_fraction)

    def test_canonical_integer_tokens_round_trip(self):
        for token in ('99', '-1', '9007199254740991'):
            with self.subTest(token=token):
                parsed = json.loads('[' + token + ']', parse_float=reject_fraction)
                self.assertIs(type(parsed[0]), int)
                self.assertLessEqual(abs(parsed[0]), MAX_SAFE)

    def test_float_in_nested_map_is_rejected_before_planning(self):
        payload = '{"floors":{"0":[[0,99.0,98]]}}'
        with self.assertRaisesRegex(ValueError, 'non-integer JSON numeric token'):
            json.loads(payload, parse_float=reject_fraction)


if __name__ == '__main__':
    unittest.main()
