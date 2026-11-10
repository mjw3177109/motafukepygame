"""Exercise real PNG evidence auditing through the public battle comparator.

These tests deliberately do not mock audit(): a matching state trace must not
pass when its screenshot evidence is missing or altered.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.compare_battle_traces import compare


class BattleEvidenceIntegrationTests(unittest.TestCase):
    def test_real_png_evidence_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            flash_root = root / "flash"
            candidate_root = root / "candidate"
            flash_root.mkdir()
            candidate_root.mkdir()
            flash_png = flash_root / "frame.png"
            candidate_png = candidate_root / "frame.png"
            for path in (flash_png, candidate_png):
                Image.new("RGB", (2, 2), (12, 34, 56)).save(path, format="PNG")

            base = dict(schema_version=1, case_id="win_001", step=0,
                        action="initial", floor=0, x=1, y=2, hp=100,
                        money=0, exp=0, monster_id="1",
                        monster_present=True, battle_phase="idle",
                        game_over=False, evidence_frame="frame.png",
                        verified=True)
            flash = dict(base, source="flash",
                         evidence_sha256=hashlib.sha256(flash_png.read_bytes()).hexdigest())
            candidate = dict(base, source="pygame",
                             evidence_sha256=hashlib.sha256(candidate_png.read_bytes()).hexdigest())
            flash_trace = root / "flash.jsonl"
            candidate_trace = root / "candidate.jsonl"
            flash_trace.write_text(json.dumps(flash) + "\n", encoding="utf-8")
            candidate_trace.write_text(json.dumps(candidate) + "\n", encoding="utf-8")

            self.assertEqual(compare(flash_trace, candidate_trace, flash_root, candidate_root), [])
            # Exercise the HTML5 path with real PNG evidence, not a mocked audit.
            candidate["source"] = "html5"
            candidate_trace.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
            self.assertEqual(compare(flash_trace, candidate_trace, flash_root, candidate_root), [])
            # A valid PNG must not conceal a gameplay-state discrepancy.
            candidate["hp"] = 99
            candidate_trace.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
            self.assertIn("hp differs", str(compare(flash_trace, candidate_trace, flash_root, candidate_root)))
            candidate["hp"] = 100
            candidate_trace.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
            candidate_png.write_bytes(b"tampered")
            self.assertIn("evidence SHA256 mismatch",
                          str(compare(flash_trace, candidate_trace, flash_root, candidate_root)))
            candidate_png.unlink()
            self.assertIn("missing or escaped evidence file",
                          str(compare(flash_trace, candidate_trace, flash_root, candidate_root)))


if __name__ == "__main__":
    unittest.main()
