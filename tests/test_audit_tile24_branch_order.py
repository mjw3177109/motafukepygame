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
      if(Number(_root.mt_GetMoney[0]) == 1)
      {
         _root.mtsay_001.gotoAndPlay("say_four");
         _root.mt_line_20[7][5] = 13;
      }
      else
      {
         _root.mtsay_001.gotoAndPlay("say_two");
         _root.mt_line_20[7][5] = 13;
      }
      _root.my_love = 0;
      _root.mt_changes = 0;
   }
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.Now_line == 22)
   {
      _root.Now_key_flag = 0;
      _root.Display_say[0] = 1;
      _root.CopyMovie("mt_say_01","mtsay_001",1350,380,207);
      if(Number(_root.mt_GetMoney[0]) == 1 && Number(_root.mt_GetMoney[1]) == 1 && Number(_root.mt_GetMoney[2]) == 1)
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
        self.assertTrue(report['love_dialogue_both_arms_verified'])
        self.assertTrue(report['floor22_three_item_both_arms_verified'])
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


    def test_love_reset_cannot_move_into_item_if_arm(self):
        changed = SOURCE.replace(
            '         _root.mt_line_20[7][5] = 13;\n      }\n      else',
            '         _root.mt_line_20[7][5] = 13;\n         _root.my_love = 0;\n      }\n      else')
        changed = changed.replace('      _root.my_love = 0;\n      _root.mt_changes = 0;',
                                  '      _root.mt_changes = 0;')
        with self.assertRaisesRegex(ValueError, 'missing shared post-choice reset'):
            verify_tile24_branch_order(changed)

    def test_love_reset_cannot_move_into_item_else_arm(self):
        changed = SOURCE.replace(
            '         _root.mt_line_20[7][5] = 13;\n      }\n      _root.my_love = 0;',
            '         _root.mt_line_20[7][5] = 13;\n         _root.mt_changes = 0;\n      }\n      _root.my_love = 0;')
        changed = changed.replace('      _root.my_love = 0;\n      _root.mt_changes = 0;',
                                  '      _root.my_love = 0;')
        with self.assertRaisesRegex(ValueError, 'missing shared post-choice reset'):
            verify_tile24_branch_order(changed)

    def test_love_reset_nested_after_choice_is_rejected(self):
        changed = SOURCE.replace(
            '      _root.my_love = 0;\n      _root.mt_changes = 0;',
            '      if(_root.Now_line == 22)\n      {\n'
            '         _root.my_love = 0;\n      }\n'
            '      _root.mt_changes = 0;')
        with self.assertRaisesRegex(ValueError, 'missing shared post-choice reset'):
            verify_tile24_branch_order(changed)

    def test_changes_reset_nested_after_choice_is_rejected(self):
        changed = SOURCE.replace(
            '      _root.my_love = 0;\n      _root.mt_changes = 0;',
            '      _root.my_love = 0;\n'
            '      if(_root.Now_line == 22)\n      {\n'
            '         _root.mt_changes = 0;\n      }')
        with self.assertRaisesRegex(ValueError, 'missing shared post-choice reset'):
            verify_tile24_branch_order(changed)

    def test_shared_reset_order_cannot_be_swapped(self):
        changed = SOURCE.replace(
            '      _root.my_love = 0;\n      _root.mt_changes = 0;',
            '      _root.mt_changes = 0;\n      _root.my_love = 0;')
        self.assertNotEqual(changed, SOURCE)
        with self.assertRaisesRegex(ValueError, 'shared reset order'):
            verify_tile24_branch_order(changed)

    def test_love_else_dialogue_cannot_be_replaced_by_first_arm(self):
        changed = SOURCE.replace('gotoAndPlay("say_two")', 'gotoAndPlay("say_four")')
        with self.assertRaisesRegex(ValueError, 'love_dialogue else arm'):
            verify_tile24_branch_order(changed)

    def test_love_else_map_write_cannot_be_lost(self):
        changed = SOURCE.replace(
            'gotoAndPlay("say_two");\n         _root.mt_line_20[7][5] = 13;',
            'gotoAndPlay("say_two");\n         _root.mt_line_20[7][5] = 12;')
        with self.assertRaisesRegex(ValueError, 'love_dialogue else arm'):
            verify_tile24_branch_order(changed)

    def test_love_if_arm_dialogue_cannot_be_replaced(self):
        changed = SOURCE.replace('gotoAndPlay("say_four")', 'gotoAndPlay("say_two")')
        with self.assertRaisesRegex(ValueError, 'love_dialogue if arm'):
            verify_tile24_branch_order(changed)

    def test_love_else_must_remain_else(self):
        changed = SOURCE.replace(
            '      else\n      {\n         _root.mtsay_001.gotoAndPlay("say_two");',
            '      if(true)\n      {\n         _root.mtsay_001.gotoAndPlay("say_two");')
        with self.assertRaisesRegex(ValueError, 'love_dialogue missing else arm'):
            verify_tile24_branch_order(changed)



    def test_floor22_missing_item_two_guard_fails(self):
        changed = SOURCE.replace(' && Number(_root.mt_GetMoney[2]) == 1', '')
        with self.assertRaisesRegex(ValueError, 'floor22_dialogue missing exact three-item AND guard'):
            verify_tile24_branch_order(changed)

    def test_floor22_wrong_item_index_fails(self):
        changed = SOURCE.replace('Number(_root.mt_GetMoney[1]) == 1', 'Number(_root.mt_GetMoney[3]) == 1')
        with self.assertRaisesRegex(ValueError, 'floor22_dialogue missing exact three-item AND guard'):
            verify_tile24_branch_order(changed)

    def test_floor22_else_dialogue_wrong_fails(self):
        changed = SOURCE.replace('gotoAndPlay("say_five")', 'gotoAndPlay("say_six")')
        with self.assertRaisesRegex(ValueError, 'floor22_dialogue else arm'):
            verify_tile24_branch_order(changed)

    def test_floor22_if_dialogue_wrong_fails(self):
        changed = SOURCE.replace('gotoAndPlay("say_six")', 'gotoAndPlay("say_five")')
        with self.assertRaisesRegex(ValueError, 'floor22_dialogue if arm'):
            verify_tile24_branch_order(changed)

    def test_floor22_else_must_remain_else(self):
        changed = SOURCE.replace(
            '      else\n      {\n         _root.mtsay_001.gotoAndPlay("say_five");',
            '      if(true)\n      {\n         _root.mtsay_001.gotoAndPlay("say_five");')
        with self.assertRaisesRegex(ValueError, 'floor22_dialogue missing else arm'):
            verify_tile24_branch_order(changed)

    def test_floor22_setup_must_precede_item_choice(self):
        changed = SOURCE.replace(
            '      _root.Now_key_flag = 0;\n      _root.Display_say[0] = 1;\n      _root.CopyMovie("mt_say_01","mtsay_001",1350,380,207);\n      if(Number(_root.mt_GetMoney[0])',
            '      _root.Now_key_flag = 0;\n      _root.CopyMovie("mt_say_01","mtsay_001",1350,380,207);\n      if(Number(_root.mt_GetMoney[0])')
        with self.assertRaisesRegex(ValueError, 'floor22_dialogue missing or duplicated pre-choice setup'):
            verify_tile24_branch_order(changed)

    def test_floor22_setup_order_must_match_original(self):
        changed = SOURCE.replace(
            '      _root.Now_key_flag = 0;\n      _root.Display_say[0] = 1;\n      _root.CopyMovie',
            '      _root.Display_say[0] = 1;\n      _root.Now_key_flag = 0;\n      _root.CopyMovie')
        with self.assertRaisesRegex(ValueError, 'pre-choice setup order'):
            verify_tile24_branch_order(changed)

    def test_floor22_duplicate_setup_write_fails_closed(self):
        changed = SOURCE.replace(
            '      _root.Now_key_flag = 0;\n      _root.Display_say[0] = 1;\n      _root.CopyMovie',
            '      _root.Now_key_flag = 0;\n      _root.Display_say[0] = 1;\n      _root.Display_say[0] = 1;\n      _root.CopyMovie')
        with self.assertRaisesRegex(ValueError, 'missing or duplicated pre-choice setup'):
            verify_tile24_branch_order(changed)


    def test_comment_braces_do_not_hide_shared_resets(self):
        changed = SOURCE.replace(
            '      _root.my_love = 0;\n      _root.mt_changes = 0;',
            '      /* } { */\n      _root.my_love = 0;\n      _root.mt_changes = 0;')
        self.assertTrue(verify_tile24_branch_order(changed)['independent_if_statements_verified'])

    def test_multiline_comment_braces_do_not_hide_shared_resets(self):
        changed = SOURCE.replace(
            '      _root.my_love = 0;\n      _root.mt_changes = 0;',
            '      /* }\n         { */\n      _root.my_love = 0;\n      _root.mt_changes = 0;')
        self.assertTrue(verify_tile24_branch_order(changed)['independent_if_statements_verified'])

    def test_string_brace_does_not_close_branch(self):
        changed = SOURCE.replace(
            '      _root.my_love = 0;\n      _root.mt_changes = 0;',
            '      trace("}");\n      _root.my_love = 0;\n      _root.mt_changes = 0;')
        self.assertTrue(verify_tile24_branch_order(changed)['independent_if_statements_verified'])


if __name__ == '__main__':
    unittest.main()
