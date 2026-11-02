"""Synthetic source tests; never interpreted as Flash execution."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import audit_terminal_guard_paths as audit
from tools import audit_terminal_candidates as base

INIT = "mt_LastGame_ID = 0;\n"
CONTROL = '''if(Number(eval(temp_lines)[temp_x][temp_y]) == 129 && _root.Display_say[8] == 0)
{
   _root.Now_key_flag = 0;
   _root.Display_say[8] = 1;
   _root.CopyMovie("mt_say_08","mtsay_008",1350,380,207);
}
if(Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.mt_changes == 1 && _root.my_love == 0)
{
   _root.Now_key_flag = 0;
   _root.Display_say[0] = 1;
   _root.CopyMovie("mt_say_01","mtsay_001",1350,380,207);
   _root.mtsay_001.gotoAndPlay("say_three");
   _root.mt_GetMoney[0] = 1;
   _root.mt_changes = 0;
   _root.mt_LastGame_ID = 1;
}
function SaveData()
{
   var temp_i = 0;
   while(temp_i < _root.save_Display_say.length)
   {
      _root.save_Display_say[temp_i] = Number(_root.Display_say[temp_i]);
      temp_i++;
   }
   _root.save_mt_LastGame_ID = Number(_root.mt_LastGame_ID);
}
function LoadData()
{
   var temp_i = 0;
   while(temp_i < _root.save_Display_say.length)
   {
      _root.Display_say[temp_i] = Number(_root.save_Display_say[temp_i]);
      temp_i++;
   }
   _root.mt_LastGame_ID = Number(_root.save_mt_LastGame_ID);
}
'''


class TerminalGuardPathsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.swf = b"synthetic original"
        self.swf_sha = hashlib.sha256(self.swf).hexdigest()
        patcher = patch.object(base, "SWF_SHA256", self.swf_sha)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.sources = {audit.INIT: INIT, audit.CONTROL: CONTROL}

    def manifest(self):
        files = []
        for path, content in self.sources.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = content.encode("utf-8")
            target.write_bytes(raw)
            files.append({"path": path, "size": len(raw),
                          "sha256": hashlib.sha256(raw).hexdigest()})
        return {"original": {"sha256": self.swf_sha}, "files": files}

    def run_audit(self):
        return audit.audit_paths(self.manifest(), self.root, self.swf)

    def test_static_guard_and_save_load_sources_verified_without_runtime_claims(self):
        result = self.run_audit()
        self.assertEqual(result["say08_start_event"]["tile_id"], 129)
        self.assertEqual(result["say08_start_event"]["required_Display_say_8"], 0)
        self.assertEqual(result["say08_start_event"]["assigned_Display_say_8"], 1)
        self.assertEqual(result["say08_start_event"]["created_clip"], "mtsay_008")
        self.assertTrue(result["say08_start_event"]["same_guarded_block_verified"])
        self.assertEqual(result["tile_event"]["assigned_mt_LastGame_ID"], 1)
        self.assertTrue(result["tile_event"]["same_guarded_block_verified"])
        self.assertEqual(result["initial"]["value"], 0)
        self.assertEqual(len(result["save_load"]), 6)
        self.assertFalse(result["runtime_branch_reachability_verified"])
        self.assertFalse(result["save_data_roundtrip_executed"])
        self.assertFalse(result["flash_ending_verified"])
        self.assertFalse(result["gymnasium_ready"])

    def test_crlf_source_is_accepted(self):
        self.sources = {k: v.replace("\n", "\r\n") for k, v in self.sources.items()}
        self.assertTrue(self.run_audit()["source_anchors_verified"])

    def test_say08_start_wrong_tile_fails_closed(self):
        self.sources[audit.CONTROL] = CONTROL.replace("== 129 &&", "== 128 &&")
        with self.assertRaisesRegex(ValueError, "tile-129 say-08 start"):
            self.run_audit()

    def test_say08_start_wrong_initial_state_fails_closed(self):
        self.sources[audit.CONTROL] = CONTROL.replace(
            "_root.Display_say[8] == 0", "_root.Display_say[8] == 1")
        with self.assertRaisesRegex(ValueError, "tile-129 say-08 start"):
            self.run_audit()

    def test_say08_start_wrong_clip_fails_closed(self):
        self.sources[audit.CONTROL] = CONTROL.replace(
            '"mt_say_08","mtsay_008"', '"mt_say_07","mtsay_008"')
        with self.assertRaisesRegex(ValueError, "tile-129 say-08 start"):
            self.run_audit()

    def test_say08_start_assignment_outside_guard_fails_closed(self):
        self.sources[audit.CONTROL] = CONTROL.replace(
            '   _root.Display_say[8] = 1;\n   _root.CopyMovie("mt_say_08"',
            '}\n_root.Display_say[8] = 1;\n   _root.CopyMovie("mt_say_08"')
        with self.assertRaisesRegex(ValueError, "tile-129 say-08 start"):
            self.run_audit()

    def test_wrong_event_guard_fails_closed(self):
        self.sources[audit.CONTROL] = CONTROL.replace("_root.my_love == 0", "_root.my_love == 1")
        with self.assertRaisesRegex(ValueError, "tile-24 guarded"):
            self.run_audit()

    def test_event_write_moved_outside_guard_fails_closed(self):
        self.sources[audit.CONTROL] = CONTROL.replace(
            "   _root.mt_LastGame_ID = 1;\n}", "}\n_root.mt_LastGame_ID = 1;")
        with self.assertRaisesRegex(ValueError, "tile-24 guarded"):
            self.run_audit()

    def test_save_load_wrong_direction_fails_closed(self):
        self.sources[audit.CONTROL] = CONTROL.replace(
            "_root.mt_LastGame_ID = Number(_root.save_mt_LastGame_ID);",
            "_root.save_mt_LastGame_ID = Number(_root.mt_LastGame_ID);")
        with self.assertRaisesRegex(ValueError, "load_terminal_guard"):
            self.run_audit()

    def test_dialogue_array_missing_fails_closed(self):
        self.sources[audit.CONTROL] = CONTROL.replace(
            "_root.Display_say[temp_i] = Number(_root.save_Display_say[temp_i]);",
            "_root.Display_say[temp_i] = 0;")
        with self.assertRaisesRegex(ValueError, "load_dialogue_array"):
            self.run_audit()

    def test_save_write_outside_function_fails_closed(self):
        self.sources[audit.CONTROL] = CONTROL.replace(
            "   _root.save_mt_LastGame_ID = Number(_root.mt_LastGame_ID);\n}",
            "}\n_root.save_mt_LastGame_ID = Number(_root.mt_LastGame_ID);")
        with self.assertRaisesRegex(ValueError, "save_terminal_guard"):
            self.run_audit()

    def test_manifest_tampering_fails_closed(self):
        manifest = self.manifest()
        (self.root / audit.CONTROL).write_text(CONTROL.replace("mt_changes == 1", "mt_changes == 2"))
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            audit.audit_paths(manifest, self.root, self.swf)

    def test_wrong_original_swf_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            audit.audit_paths(self.manifest(), self.root, b"other SWF")


if __name__ == "__main__":
    unittest.main()
