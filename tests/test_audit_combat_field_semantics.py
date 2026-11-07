"""Synthetic mutation tests; these are not recorded Flash playthroughs."""
import hashlib
import unittest

from tools.audit_combat_field_semantics import audit_combat_field_semantics

SCRIPT = '''
_root.mt_kills.left_hp = _root.boss_man[_root.Now_boss_id][0];
_root.mt_kills.left_gong = _root.boss_man[_root.Now_boss_id][1];
_root.mt_kills.left_fang = _root.boss_man[_root.Now_boss_id][2];
_root.Now_money += _root.boss_man[_root.Now_boss_id][3];
_root.Now_mp += _root.boss_man[_root.Now_boss_id][4];
tmp_kills = int(_root.boss_man[tmp_boss][0] / (_root.Now_gong - _root.boss_man[tmp_boss][2])) * (_root.boss_man[tmp_boss][1] - _root.Now_fang);
if(_root.boss_man[tmp_boss][2] >= _root.Now_gong) { kill_flag = 0; }
else if(tmp_kills > _root.Now_hp) { kill_flag = 0; }
switch(tmp_boss) {
case 20: tmp_kills += 100; break;
case 12: tmp_kills += 300; break;
case 10: tmp_kills += int(_root.Now_hp / 4); break;
case 17: tmp_kills += int(_root.Now_hp / 3);
}
'''


class OriginalCombatSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.script = SCRIPT.encode()
        self.swf = b'synthetic SWF, not original game.swf'
        swf_hash = hashlib.sha256(self.swf).hexdigest()
        self.floors = {'source': {'swf_sha256': swf_hash,
            'renderer_actionscript_path': 'export/scripts/frame_4346/DoAction_2.as',
            'renderer_actionscript_sha256': hashlib.sha256(self.script).hexdigest()}}
        self.combat = {'source': {'swf_sha256': swf_hash}}

    def check(self):
        return audit_combat_field_semantics(self.script, self.swf, self.floors, self.combat)

    def replace_and_reanchor(self, old, new):
        self.script = self.script.replace(old.encode(), new.encode())
        self.floors['source']['renderer_actionscript_sha256'] = hashlib.sha256(self.script).hexdigest()

    def test_five_roles_four_specials_and_closed_gates(self):
        report = self.check()
        self.assertEqual(report['field_roles'], {'monster_hp': 0, 'monster_attack': 1,
            'monster_defense': 2, 'gold_reward': 3, 'experience_reward': 4})
        self.assertEqual(set(report['special_entry_bonuses']), {'20', '12', '10', '17'})
        for gate in ('full_battle_verified', 'flash_replay_verified', 'gameplay_parity_verified',
                     'gymnasium_ready', 'kaggle_started'):
            self.assertIs(report[gate], False)

    def test_rejects_swapped_reward_field_even_if_rehashed(self):
        self.replace_and_reanchor('Now_money += _root.boss_man[_root.Now_boss_id][3]',
                                  'Now_money += _root.boss_man[_root.Now_boss_id][4]')
        with self.assertRaisesRegex(ValueError, 'gold_reward'):
            self.check()

    def test_rejects_changed_damage_formula_even_if_rehashed(self):
        self.replace_and_reanchor('(_root.boss_man[tmp_boss][1] - _root.Now_fang)',
                                  '(_root.boss_man[tmp_boss][1] + _root.Now_fang)')
        with self.assertRaisesRegex(ValueError, 'loss expression'):
            self.check()

    def test_rejects_changed_special_bonus_even_if_rehashed(self):
        self.replace_and_reanchor('tmp_kills += 300', 'tmp_kills += 301')
        with self.assertRaisesRegex(ValueError, 'special-loss'):
            self.check()

    def test_rejects_changed_hp_gate_even_if_rehashed(self):
        self.replace_and_reanchor('tmp_kills > _root.Now_hp', 'tmp_kills >= _root.Now_hp')
        with self.assertRaisesRegex(ValueError, 'HP entry gate'):
            self.check()

    def test_rejects_hash_drift_and_swf_replacement(self):
        self.script += b'// altered'
        with self.assertRaisesRegex(ValueError, 'ActionScript hash mismatch'):
            self.check()
        self.script = SCRIPT.encode()
        self.swf = b'replaced SWF'
        with self.assertRaisesRegex(ValueError, 'SWF hash mismatch'):
            self.check()


if __name__ == '__main__':
    unittest.main()
