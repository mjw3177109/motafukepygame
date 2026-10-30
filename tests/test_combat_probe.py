"""Independent expected results from the original Move_arrow branch."""
import json
import unittest
from pathlib import Path

from core.combat_probe import preview_encounter

CASES = json.loads((Path(__file__).parent / 'fixtures' / 'combat_probe_cases.json').read_text(encoding='utf-8'))


class CombatProbeTests(unittest.TestCase):
    def test_original_combat_vectors(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                original = json.dumps(case, ensure_ascii=False, sort_keys=True)
                self.assertEqual(preview_encounter(case['tile'], case['monster'], case['hero']), case['expected'])
                self.assertEqual(json.dumps(case, ensure_ascii=False, sort_keys=True), original)

    def test_reject_non_monster_tile(self):
        with self.assertRaisesRegex(ValueError, 'monster tile'):
            preview_encounter(71, CASES[0]['monster'], CASES[0]['hero'])

    def test_reject_missing_monster_stats(self):
        with self.assertRaisesRegex(ValueError, 'six-field'):
            preview_encounter(40, [50,20], CASES[0]['hero'])


if __name__ == '__main__':
    unittest.main()
