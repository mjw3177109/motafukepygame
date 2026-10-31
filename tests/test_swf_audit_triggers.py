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
    'core/floor_render.py',
    'core/static_svg_assets.py',
    'core/verified_static_preview.py',
    'tests/test_floor_render.py',
    'tests/test_static_svg_assets.py',
    'tests/test_verified_static_preview.py',
    'tests/test_smoke_original_static_render.py',
    'tests/test_smoke_original_browser_static.py',
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

    def test_push_and_pr_filters_are_identical_and_unique(self):
        # A source-only change must never silently skip one of the two audits.
        trigger_block = self.text.split('\npermissions:', 1)[0]
        push = trigger_block.split('\n  push:', 1)[1].split('\n  pull_request:', 1)[0]
        pr = trigger_block.split('\n  pull_request:', 1)[1]

        def paths(section):
            return [line.strip()[3:-1] for line in section.splitlines()
                    if line.strip().startswith("- '") and line.strip().endswith("'")]

        push_paths, pr_paths = paths(push), paths(pr)
        self.assertEqual(push_paths, pr_paths)
        self.assertEqual(len(push_paths), len(set(push_paths)))

    def test_provenance_verification_remains_in_job(self):
        self.assertIn('python tools/verify_original_floors.py --committed data/original_floors.json', self.text)
        self.assertIn('python tools/package_swf_audit.py', self.text)
        self.assertIn("java-version: '8'", self.text)


if __name__ == '__main__':
    unittest.main()
