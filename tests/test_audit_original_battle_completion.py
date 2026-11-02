"""Fail-closed tests for original battle completion source pinning."""
import hashlib
import unittest
from unittest.mock import patch
from tools import audit_original_battle_completion as audit

COMPLETION = b'''if(_root.Display_kill == 2) {
_root.DelMovie("mt_kills");
_root.DelMovie("mt_kills_left");
_root.DelMovie("mt_kills_right");
_root.Display_kill = 0;
_root.Move_arrow(100);
}'''
REWARD = b'''if(arrow_id == 100) {
_root.Display_text = 1;
_root.Now_money += _root.boss_man[_root.Now_boss_id][3];
_root.Now_mp += _root.boss_man[_root.Now_boss_id][4];
_root.mt_Mylife.My_hp = _root.Now_hp;
}'''


class CompletionAuditTests(unittest.TestCase):
    def setUp(self):
        self.scripts = {'completion': COMPLETION, 'reward': REWARD}
        self.anchors = {k: (audit.SOURCES[k][0], hashlib.sha256(v).hexdigest())
                        for k, v in self.scripts.items()}
        self.patch = patch.object(audit, 'SOURCES', self.anchors)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        block = audit._block(COMPLETION.decode(), r'_root\.Display_kill\s*==\s*2')
        self.block_patch = patch.object(audit, 'COMPLETION_BLOCK_SHA256', hashlib.sha256(block.encode()).hexdigest())
        self.block_patch.start()
        self.addCleanup(self.block_patch.stop)

    def test_source_scoped_chain_is_explicitly_not_flash_parity(self):
        report = audit.audit_completion(self.scripts, audit.SWF_SHA256)
        self.assertTrue(report['no_hp_guard_in_these_two_blocks'])
        self.assertFalse(report['global_death_handling_verified'])
        self.assertFalse(report['negative_hp_runtime_verified'])
        self.assertFalse(report['gymnasium_ready'])

    def test_rejects_swf_identity_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'game.swf'):
            audit.audit_completion(self.scripts, 'bad')

    def test_rejects_modified_actionscript_bytes(self):
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            audit.audit_completion({**self.scripts, 'reward': REWARD + b' '}, audit.SWF_SHA256)

    def test_rejects_missing_completion_dispatch(self):
        changed = COMPLETION.replace(b'_root.Move_arrow(100);', b'')
        with patch.dict(audit.SOURCES, {'completion': (self.anchors['completion'][0], hashlib.sha256(changed).hexdigest())}):
            with self.assertRaisesRegex(ValueError, 'completion source block SHA256'):
                audit.audit_completion({**self.scripts, 'completion': changed}, audit.SWF_SHA256)

    def test_rejects_new_hp_guard(self):
        changed = REWARD.replace(b'_root.Display_text = 1;', b'if(_root.Now_hp <= 0) { return; }\n_root.Display_text = 1;')
        with patch.dict(audit.SOURCES, {'reward': (self.anchors['reward'][0], hashlib.sha256(changed).hexdigest())}):
            with self.assertRaisesRegex(ValueError, 'HP conditional'):
                audit.audit_completion({**self.scripts, 'reward': changed}, audit.SWF_SHA256)

    def test_rejects_missing_reward(self):
        changed = REWARD.replace(b'_root.Now_mp += _root.boss_man[_root.Now_boss_id][4];', b'')
        with patch.dict(audit.SOURCES, {'reward': (self.anchors['reward'][0], hashlib.sha256(changed).hexdigest())}):
            with self.assertRaisesRegex(ValueError, 'reward clause'):
                audit.audit_completion({**self.scripts, 'reward': changed}, audit.SWF_SHA256)


if __name__ == '__main__':
    unittest.main()
