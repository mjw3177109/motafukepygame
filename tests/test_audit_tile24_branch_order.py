"""Synthetic, fail-closed tile-24 source tests; not a Flash runtime test."""
import unittest
from tools.audit_tile24_branch_order import verify_tile24_branch_order

SOURCE = '''function Move_arrow(arrow_id)
{
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.Display_say[0] == 0)
   {
      _root.Display_say[0] = 1;
      _root.CopyMovie("mt_say_01","mtsay_001",1350,380,207);
   }
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.mt_changes == 1 && _root.my_love == 0)
   {
      _root.mtsay_001.gotoAndPlay("say_three");
      _root.mt_changes = 0;
      _root.mt_LastGame_ID = 1;
   }
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.my_love == 1)
   {
      if(_root.flag)
      {
         _root.mt_line_20[7][5] = 13;
      }
      _root.my_love = 0;
      _root.mt_changes = 0;
   }
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.Now_line == 22)
   {
      if(_root.flag)
      {
         _root.mtsay_001.gotoAndPlay("say_six");
      }
      else
      {
         _root.mtsay_001.gotoAndPlay("say_five");
      }
   }
}
'''


class Tile24BranchOrderTests(unittest.TestCase):
    def test_original_independent_guard_order(self):
        report = verify_tile24_branch_order(SOURCE)
        self.assertEqual([item['branch'] for item in report['source_order']],
                         ['initial_dialogue', 'ending_state_change', 'love_dialogue', 'floor22_dialogue'])
        self.assertTrue(report['independent_if_statements_verified'])
        self.assertFalse(report['runtime_combined_branch_execution_verified'])
        self.assertFalse(report['flash_parity_verified'])

    def test_crlf(self):
        self.assertTrue(verify_tile24_branch_order(SOURCE.replace('\n', '\r\n'))['independent_if_statements_verified'])

    def test_wrong_guard_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'ending_state_change guard'):
            verify_tile24_branch_order(SOURCE.replace('_root.mt_changes == 1 &&', '_root.mt_changes == 2 &&'))

    def test_reordered_guards_fail_closed(self):
        first = SOURCE.index('   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.Display_say')
        second = SOURCE.index('   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.mt_changes')
        third = SOURCE.index('   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.my_love')
        changed = SOURCE[:first] + SOURCE[second:third] + SOURCE[first:second] + SOURCE[third:]
        with self.assertRaisesRegex(ValueError, 'guard order'):
            verify_tile24_branch_order(changed)

    def test_missing_ending_write_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'missing branch statement'):
            verify_tile24_branch_order(SOURCE.replace('_root.mt_LastGame_ID = 1;', '_root.mt_LastGame_ID = 0;'))

    def test_write_moved_to_other_guard_fails_closed(self):
        changed = SOURCE.replace('      _root.mt_LastGame_ID = 1;\n', '')
        changed = changed.replace('      _root.my_love = 0;', '      _root.mt_LastGame_ID = 1;\n      _root.my_love = 0;')
        with self.assertRaisesRegex(ValueError, 'ending_state_change missing branch statement'):
            verify_tile24_branch_order(changed)

    def test_comment_cannot_fake_required_write(self):
        changed = SOURCE.replace('      _root.mt_LastGame_ID = 1;', '      // _root.mt_LastGame_ID = 1;')
        with self.assertRaisesRegex(ValueError, 'missing branch statement'):
            verify_tile24_branch_order(changed)

    def test_duplicate_guard_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'expected four independent'):
            verify_tile24_branch_order(SOURCE.replace(
                '   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.my_love == 1)',
                '   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.my_love == 1)\n   {}\n   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.my_love == 1)'))


if __name__ == '__main__':
    unittest.main()
