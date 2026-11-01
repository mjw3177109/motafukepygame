"""Synthetic fixtures only: no test fixture is claimed as original Flash data."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.verify_original_combat_tables import verify_original_combat_tables, SOURCE_PATH


class RawCombatTablesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        script = self.root / SOURCE_PATH
        script.parent.mkdir(parents=True)
        script.write_bytes(b'synthetic test ActionScript')
        digest = hashlib.sha256(script.read_bytes()).hexdigest()
        swf = self.root / 'game.swf'
        swf.write_bytes(b'synthetic test SWF')
        source = {'swf_sha256': hashlib.sha256(swf.read_bytes()).hexdigest(), 'actionscript_sha256': digest,
                  'actionscript_path': SOURCE_PATH}
        self.extracted = {'schema_version': 1, 'source': copy.deepcopy(source),
                          'monster_field_order': 'raw ActionScript array order; meanings require independent verification',
                          'monsters': {str(i): [i, 20, 3, 4, 5, f'fixture-{i}'] for i in range(33)},
                          'base_stats': {k: i for i, k in enumerate(('life', 'hp', 'gong', 'fang', 'money', 'yellow', 'blue', 'red', 'mp'))}}
        self.committed = copy.deepcopy(self.extracted)
        self.committed.update({k: False for k in ('combat_formula_verified', 'gameplay_parity_verified', 'gymnasium_ready', 'kaggle_started')})
        self.floors = {'schema_version': 1, 'source': copy.deepcopy(source)}

    def verify(self):
        return verify_original_combat_tables(self.committed, self.extracted, self.floors, self.root, self.root / 'game.swf')

    def test_valid_raw_arrays_do_not_claim_formula_or_gameplay(self):
        result = self.verify()
        self.assertEqual((result['monster_count'], result['base_stat_count']), (33, 9))
        self.assertFalse(result['combat_formula_verified'])
        self.assertFalse(result['gymnasium_ready'])

    def test_rejects_monster_numeric_drift_at_exact_field(self):
        self.committed['monsters']['12'][2] = 99
        with self.assertRaisesRegex(ValueError, r'12\[2\]'):
            self.verify()

    def test_rejects_monster_name_drift(self):
        self.committed['monsters']['3'][5] = 'modified'
        with self.assertRaisesRegex(ValueError, r'3\[5\]'):
            self.verify()

    def test_rejects_base_stat_drift(self):
        self.committed['base_stats']['hp'] += 1
        with self.assertRaisesRegex(ValueError, 'base stat drift at hp'):
            self.verify()

    def test_rejects_missing_monster_and_bool_field(self):
        del self.extracted['monsters']['32']
        with self.assertRaisesRegex(ValueError, 'monster ids'):
            self.verify()
        self.extracted['monsters']['32'] = [32, 20, 3, 4, 5, 'fixture-32']
        self.extracted['monsters']['0'][0] = True
        with self.assertRaisesRegex(ValueError, 'invalid raw monster'):
            self.verify()

    def test_rejects_missing_or_bool_base_stat(self):
        del self.extracted['base_stats']['mp']
        with self.assertRaisesRegex(ValueError, 'nine original base stats'):
            self.verify()
        self.extracted['base_stats']['mp'] = True
        with self.assertRaisesRegex(ValueError, 'noninteger base stat'):
            self.verify()

    def test_rejects_swapped_original_swf_bytes(self):
        (self.root / 'game.swf').write_bytes(b'changed SWF')
        with self.assertRaisesRegex(ValueError, 'SWF bytes hash mismatch'):
            self.verify()

    def test_rejects_missing_original_swf(self):
        (self.root / 'game.swf').unlink()
        with self.assertRaisesRegex(ValueError, 'missing original SWF'):
            self.verify()

    def test_rejects_script_hash_and_independent_anchor_drift(self):
        (self.root / SOURCE_PATH).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'export hash mismatch'):
            self.verify()
        self.floors['source']['swf_sha256'] = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'swf_sha256 anchor mismatch'):
            self.verify()

    def test_rejects_unsafe_path_and_false_approval(self):
        self.extracted['source']['actionscript_path'] = '../../outside.as'
        with self.assertRaisesRegex(ValueError, 'path mismatch'):
            self.verify()
        self.extracted['source']['actionscript_path'] = SOURCE_PATH
        self.committed['gymnasium_ready'] = True
        with self.assertRaisesRegex(ValueError, 'unsafe or missing acceptance gate'):
            self.verify()

    def test_rejects_missing_field_order_or_missing_gate(self):
        self.committed['monster_field_order'] = 'guessed meanings'
        with self.assertRaisesRegex(ValueError, 'field order'):
            self.verify()
        self.committed['monster_field_order'] = self.extracted['monster_field_order']
        del self.committed['combat_formula_verified']
        with self.assertRaisesRegex(ValueError, 'acceptance gate'):
            self.verify()


if __name__ == '__main__':
    unittest.main()
