"""Contract tests for the first JSON-to-spawn handoff (not Flash parity)."""
import json
import hashlib
import unittest
from pathlib import Path
from core.initial_floor_loader import (
    plan_committed_floor_00_spawn, EXPECTED_SWF_SHA256, EXPECTED_ACTIONSCRIPT_SHA256,
    EXPECTED_RENDERER_SHA256,
)


def payload():
    floor = [[0] * 11 for _ in range(11)]
    floor[9][5] = 99
    floor[1][5] = 98
    return {'schema_version': 1, 'source': {
        'swf_sha256': EXPECTED_SWF_SHA256,
        'actionscript_sha256': EXPECTED_ACTIONSCRIPT_SHA256,
        'renderer_actionscript_sha256': EXPECTED_RENDERER_SHA256},
        'floors': {'00': floor}}


class InitialFloorLoaderTests(unittest.TestCase):
    def test_committed_original_floor_00_handoff(self):
        """Exercise the real source-pinned map file, not only synthetic fixtures."""
        path = Path(__file__).resolve().parents[1] / 'data' / 'original_floors.json'
        plan = plan_committed_floor_00_spawn(path.read_text(encoding='utf-8'))
        self.assertEqual((plan['hero']['x'], plan['hero']['y']), (367, 335))
        self.assertEqual(plan['suppressed_98'], [{'row': 1, 'col': 5}])


    def test_committed_swf_bytes_match_floor_source_pin(self):
        """Verify real SWF bytes, not only a JSON provenance claim."""
        root = Path(__file__).resolve().parents[1]
        swf = root / 'game.swf'
        with swf.open('rb') as stream:
            actual_sha256 = hashlib.file_digest(stream, 'sha256').hexdigest()
        self.assertEqual(actual_sha256, EXPECTED_SWF_SHA256)
        data = json.loads((root / 'data' / 'original_floors.json').read_text(encoding='utf-8'))
        self.assertEqual(data['source']['swf_sha256'], actual_sha256)

    def test_valid_floor_handoff(self):
        plan = plan_committed_floor_00_spawn(json.dumps(payload()))
        self.assertEqual((plan['hero']['x'], plan['hero']['y']), (367, 335))
        self.assertEqual(plan['suppressed_98'], [{'row': 1, 'col': 5}])

    def test_reject_source_and_floor_id_drift(self):
        for mutation in ('source', 'swf', 'missing_swf', 'floor_id', 'schema', 'boolean_schema'):
            data = payload()
            if mutation == 'source':
                data['source']['renderer_actionscript_sha256'] = 'bad'
            elif mutation == 'swf':
                data['source']['swf_sha256'] = 'bad'
            elif mutation == 'missing_swf':
                del data['source']['swf_sha256']
            elif mutation == 'floor_id':
                data['floors']['0'] = data['floors'].pop('00')
            elif mutation == 'boolean_schema':
                data['schema_version'] = True
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
