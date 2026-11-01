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




class OriginalMonsterRosterMatrixTests(unittest.TestCase):
    """132 source-roster entry checks; synthetic hero states, not Flash replays."""

    @classmethod
    def setUpClass(cls):
        import hashlib
        root = Path(__file__).resolve().parents[1]
        cls.table = json.loads((root / 'data' / 'original_combat_tables.json').read_text(encoding='utf-8'))
        cls.swf_hash = hashlib.sha256((root / 'game.swf').read_bytes()).hexdigest()

    @staticmethod
    def expected_entry(enemy_id, monster, hero):
        hp, attack, defense = monster[:3]
        if hero['attack'] <= defense:
            return {'enemy_id': enemy_id, 'can_start': False, 'reason': 'insufficient_attack',
                    'base_loss': None, 'special_loss': None, 'estimated_loss': None}
        # Pinned monster HP and the attack delta are positive. Integer
        # division independently implements ActionScript int(positive ratio).
        base = (hp // (hero['attack'] - defense)) * (attack - hero['defense'])
        special = {20: 100, 12: 300, 10: hero['hp'] // 4,
                   17: hero['hp'] // 3}.get(enemy_id, 0)
        loss = base + special
        allowed = loss <= hero['hp']
        return {'enemy_id': enemy_id, 'can_start': allowed,
                'reason': 'ok' if allowed else 'insufficient_hp',
                'base_loss': base, 'special_loss': special, 'estimated_loss': loss}

    def test_source_roster_and_original_swf_hash(self):
        self.assertEqual(self.table['source']['swf_sha256'], self.swf_hash)
        self.assertEqual(set(self.table['monsters']), {str(i) for i in range(33)})
        self.assertFalse(self.table['gameplay_parity_verified'])
        self.assertFalse(self.table['gymnasium_ready'])
        for monster in self.table['monsters'].values():
            self.assertEqual(len(monster), 6)
            self.assertTrue(all(type(value) is int for value in monster[:5]))
            self.assertGreater(monster[0], 0)

    def test_all_33_monsters_four_hero_profiles(self):
        for enemy_id in range(33):
            monster = self.table['monsters'][str(enemy_id)]
            tile = enemy_id + 40 if enemy_id < 31 else 188 if enemy_id == 31 else 198
            profiles = {
                'attack_denied': {'hp': 1000, 'attack': 1, 'defense': 10},
                'ordinary': {'hp': 1000, 'attack': 200, 'defense': 50},
                'high_stats': {'hp': 100000, 'attack': 6000, 'defense': 1000},
                'one_above_defense': {'hp': 100000, 'attack': monster[2] + 1,
                                      'defense': monster[1]},
            }
            for profile_name, hero in profiles.items():
                with self.subTest(monster=enemy_id, profile=profile_name):
                    before_monster = monster.copy()
                    before_hero = hero.copy()
                    self.assertEqual(preview_encounter(tile, monster, hero),
                                     self.expected_entry(enemy_id, monster, hero))
                    self.assertEqual(monster, before_monster)
                    self.assertEqual(hero, before_hero)

if __name__ == '__main__':
    unittest.main()
