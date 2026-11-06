"""Contract tests for the first JSON-to-spawn handoff (not Flash parity)."""
import json
import unittest
from core.initial_floor_loader import (
    plan_committed_floor_00_spawn, EXPECTED_ACTIONSCRIPT_SHA256,
    EXPECTED_RENDERER_SHA256,
)


def payload():
    floor = [[0] * 11 for _ in range(11)]
    floor[9][5] = 99
    floor[1][5] = 98
    return {'schema_version': 1, 'source': {
        'actionscript_sha256': EXPECTED_ACTIONSCRIPT_SHA256,
        'renderer_actionscript_sha256': EXPECTED_RENDERER_SHA256},
        'floors': {'00': floor}}


class InitialFloorLoaderTests(unittest.TestCase):
    def test_valid_floor_handoff(self):
        plan = plan_committed_floor_00_spawn(json.dumps(payload()))
        self.assertEqual((plan['hero']['x'], plan['hero']['y']), (367, 335))
        self.assertEqual(plan['suppressed_98'], [{'row': 1, 'col': 5}])

    def test_reject_source_and_floor_id_drift(self):
        for mutation in ('source', 'floor_id', 'schema'):
            data = payload()
            if mutation == 'source':
                data['source']['renderer_actionscript_sha256'] = 'bad'
            elif mutation == 'floor_id':
                data['floors']['0'] = data['floors'].pop('00')
            else:
                data['schema_version'] = 2
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                plan_committed_floor_00_spawn(json.dumps(data))

    def test_reject_duplicate_keys_and_float_tile(self):
        raw = json.dumps(payload())
        with self.assertRaisesRegex(ValueError, 'duplicate JSON object key'):
            plan_committed_floor_00_spawn(raw.replace(
                '"schema_version": 1',
                '"schema_version": 1, "schema_version": 1'))
        data = payload()
        data['floors']['00'][9][5] = 99.0
        with self.assertRaisesRegex(ValueError, 'non-integer JSON numeric token'):
            plan_committed_floor_00_spawn(json.dumps(data))

    def test_reject_invalid_marker(self):
        data = payload()
        data['floors']['00'][9][5] = 0
        with self.assertRaisesRegex(ValueError, 'tile 99'):
            plan_committed_floor_00_spawn(json.dumps(data))


if __name__ == '__main__':
    unittest.main()
