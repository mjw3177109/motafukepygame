"""Regression guard: SWF provenance CI must run when its source inputs change.

Only stdlib is used so this test runs in the existing Python tooling CI.
"""
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/swf-audit.yml'
REQUIRED_PATHS = (
    'game.swf',
    'FFDec/**',
    'data/original_floors.json',
    'core/floor_tile_plan.py',
    'tools/**',
    '.github/workflows/swf-audit.yml',
)


class OriginalAuditTriggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding='utf-8')

    def test_pull_requests_run_original_source_audit(self):
        self.assertRegex(self.text, r'(?m)^  pull_request:\s*$')
        self.assertRegex(self.text, r'(?m)^    paths:\s*$')

    def test_push_and_pr_share_required_source_paths(self):
        trigger_block = self.text.split('\npermissions:', 1)[0]
        push = trigger_block.split('\n  push:', 1)[1].split('\n  pull_request:', 1)[0]
        pr = trigger_block.split('\n  pull_request:', 1)[1]
        for path in REQUIRED_PATHS:
            with self.subTest(path=path):
                self.assertIn(f"      - '{path}'", push)
                self.assertIn(f"      - '{path}'", pr)

    def test_provenance_verification_remains_in_job(self):
        self.assertIn('python tools/verify_original_floors.py --committed data/original_floors.json', self.text)
        self.assertIn('python tools/package_swf_audit.py', self.text)
        self.assertIn("java-version: '8'", self.text)


if __name__ == '__main__':
    unittest.main()
