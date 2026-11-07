"""Fail-closed tests for static Move_arrow source binding, not Flash execution."""
import unittest

from tools.audit_move_arrow_binding import verify_move_arrow_binding


def fixture():
    return '''function Move_arrow(arrow_id)
{
   if(_root.Now_line < 10)
   {
      temp_lines = "_root.mt_line_0" add _root.Now_line;
   }
   else
   {
      temp_lines = "_root.mt_line_" add _root.Now_line;
   }
   temp_x = _root.Now_xid;
   temp_y = _root.Now_yid;
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 0)
   {
      _root.mt_man._x = 207 + temp_y * 32;
      _root.mt_man._y = 47 + temp_x * 32;
   }
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 129 && _root.Display_say[8] == 0)
   {
   }
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.Display_say[0] == 0) {}
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.mt_changes == 1) {}
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.my_love == 1) {}
   if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.Now_line == 22) {}
}
'''


class MoveArrowBindingTests(unittest.TestCase):
    def test_static_source_evidence_and_runtime_gate(self):
        report = verify_move_arrow_binding(fixture())
        self.assertEqual(report['tile_event_lookup_counts_within_move_arrow'], {'24': 4, '129': 1})
        self.assertTrue(report['static_source_binding_verified'])
        self.assertFalse(report['runtime_floor_selection_verified'])
        self.assertFalse(report['runtime_event_reachability_verified'])

    def test_crlf_is_accepted(self):
        self.assertTrue(verify_move_arrow_binding(fixture().replace('\n', '\r\n'))['static_source_binding_verified'])

    def test_wrong_floor_selector_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'zero-padded floor selector'):
            verify_move_arrow_binding(fixture().replace('"_root.mt_line_0"', '"_root.mt_line_"'))

    def test_transposed_screen_mapping_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'screen x mapping'):
            verify_move_arrow_binding(fixture().replace('207 + temp_y * 32', '207 + temp_x * 32'))

    def test_event_lookup_removed_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'event tile 129 lookup count'):
            verify_move_arrow_binding(fixture().replace('== 129 &&', '== 128 &&'))

    def test_event_lookup_outside_function_fails_closed(self):
        source = fixture().replace('   if(Number(eval(temp_lines)[temp_x][temp_y]) == 129',
                                   '}\nif(Number(eval(temp_lines)[temp_x][temp_y]) == 129')
        with self.assertRaisesRegex(ValueError, 'event tile 129 lookup count'):
            verify_move_arrow_binding(source)

    def test_duplicate_move_arrow_function_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'exactly one Move_arrow'):
            verify_move_arrow_binding(fixture() + fixture())

    def test_unexpected_floor_reassignment_fails_closed(self):
        source = fixture().replace('   temp_x = _root.Now_xid;',
                                   '   temp_lines = "bogus";\n   temp_x = _root.Now_xid;')
        with self.assertRaisesRegex(ValueError, 'unexpected temp_lines reassignment'):
            verify_move_arrow_binding(source)


if __name__ == '__main__':
    unittest.main()
