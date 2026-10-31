import hashlib
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tools.diagnose_ffdec_script_drift import (
    byte_summary, classify, diagnose, first_difference, main, safe_renderer_path,
)


def digest(value):
    return hashlib.sha256(value).hexdigest()


class FFDecDriftDiagnosticsTests(unittest.TestCase):
    def test_matching_first_export_does_not_rerun_ffdec(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            swf, jar = root / 'game.swf', root / 'ffdec.jar'
            swf.write_bytes(b'original SWF fixture')
            jar.write_bytes(b'FFDec fixture')
            script = root / 'export/scripts/frame_4346/DoAction_2.as'
            script.parent.mkdir(parents=True)
            script.write_bytes(b'original script fixture')
            source = {'swf_sha256': digest(swf.read_bytes()),
                      'renderer_actionscript_path': 'export/scripts/frame_4346/DoAction_2.as',
                      'renderer_actionscript_sha256': digest(script.read_bytes())}
            manifest = {'original': {'sha256': source['swf_sha256']},
                        'files': [{'path': source['renderer_actionscript_path'].removeprefix('export/'),
                                   'sha256': source['renderer_actionscript_sha256']}]}
            with patch('subprocess.run', side_effect=AssertionError('must not rerun')):
                result = diagnose({'source': source}, manifest, swf, jar, root / 'export')
            self.assertTrue(result['provenance_verified'])
            self.assertEqual(result['classification'], 'first_export_matches_anchor')
            self.assertFalse(result['gameplay_parity_verified'])

    def test_matching_export_with_stale_manifest_fails_without_ffdec_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            swf, jar = root / 'game.swf', root / 'ffdec.jar'
            swf.write_bytes(b'original swf')
            jar.write_bytes(b'original ffdec')
            script = root / 'export/scripts/frame_4346/DoAction_2.as'
            script.parent.mkdir(parents=True)
            script.write_bytes(b'correct original script')
            source = {
                'swf_sha256': digest(swf.read_bytes()),
                'renderer_actionscript_path': 'export/scripts/frame_4346/DoAction_2.as',
                'renderer_actionscript_sha256': digest(script.read_bytes()),
            }
            manifest = {
                'original': {'sha256': source['swf_sha256']},
                'files': [{'path': 'scripts/frame_4346/DoAction_2.as',
                           'sha256': digest(b'stale manifest hash')}],
            }
            with patch('subprocess.run', side_effect=AssertionError('FFDec retry is not warranted')):
                result = diagnose({'source': source}, manifest, swf, jar, root / 'export')
            self.assertEqual(result['classification'],
                             'manifest_hash_mismatch_first_export_matches_anchor')
            self.assertEqual(result['first']['sha256'], source['renderer_actionscript_sha256'])
            self.assertEqual(result['manifest_sha256'], digest(b'stale manifest hash'))
            self.assertIsNone(result['repeat'])
            self.assertIsNone(result['repeat_exit_code'])
            self.assertFalse(result['provenance_verified'])
            self.assertFalse(result['gameplay_parity_verified'])
            self.assertFalse(result['kaggle_started'])

    def test_classifies_retry_evidence_without_claiming_success(self):
        anchor = digest(b'correct')
        self.assertEqual(classify(anchor, b'wrong', b'correct'),
                         'repeat_matches_anchor_first_does_not')
        self.assertEqual(classify(anchor, b'wrong', b'wrong'),
                         'repeatable_mismatch_against_anchor')
        self.assertEqual(classify(anchor, b'wrong', b'different'),
                         'two_distinct_mismatches_against_anchor')
        self.assertEqual(classify(anchor, b'wrong', None), 'mismatch_repeat_unavailable')

    def test_rejects_unsafe_paths(self):
        for name in ('../export/scripts/a.as', 'export/scripts/../a.as',
                     'export/scripts/a.py', '/export/scripts/a.as',
                     'export/scripts\\a.as'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_renderer_path(name)

    def test_byte_difference_and_line_endings(self):
        self.assertEqual(first_difference(b'abcd', b'abXd'), 2)
        self.assertEqual(first_difference(b'abc', b'abcd'), 3)
        self.assertIsNone(first_difference(b'abc', b'abc'))
        self.assertEqual(byte_summary(b'a\r\nb\n')['crlf'], 1)
        self.assertEqual(byte_summary(b'a\r\nb\n')['lf'], 2)

    def test_ci_runs_fail_closed_probe_and_archives_diagnostic(self):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/swf-audit.yml')
        self.assertTrue(workflow.is_file(), 'SWF audit workflow is required')
        content = workflow.read_text(encoding='utf-8')
        self.assertIn('python -m tools.diagnose_ffdec_script_drift', content)
        self.assertIn('.swf_audit/ffdec_script_drift_diagnostic.json', content)
        self.assertLess(content.index('python -m tools.diagnose_ffdec_script_drift'),
                        content.index('python tools/verify_original_floors.py'))

    def test_swf_mismatch_never_retries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            swf, jar = root / 'game.swf', root / 'ffdec.jar'
            swf.write_bytes(b'wrong swf')
            jar.write_bytes(b'jar')
            source = {'swf_sha256': digest(b'correct swf'),
                      'renderer_actionscript_path': 'export/scripts/frame_4346/DoAction_2.as',
                      'renderer_actionscript_sha256': digest(b'script')}
            with patch('subprocess.run', side_effect=AssertionError('must not rerun')):
                with self.assertRaisesRegex(ValueError, 'SWF provenance mismatch'):
                    diagnose({'source': source}, {'original': {'sha256': source['swf_sha256']}},
                             swf, jar, root / 'export')


    def test_cli_records_invalid_input_json_as_fail_closed_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            committed = root / 'committed.json'
            manifest = root / 'manifest.json'
            report = root / 'nested' / 'diagnostic.json'
            committed.write_text('{invalid json', encoding='utf-8')
            manifest.write_text('{}', encoding='utf-8')
            argv = ['ffdec-drift', '--committed', str(committed),
                    '--manifest', str(manifest), '--swf', str(root / 'game.swf'),
                    '--ffdec', str(root / 'ffdec.jar'),
                    '--export-root', str(root / 'export'), '--out', str(report)]
            with patch.object(sys, 'argv', argv), redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as failure:
                    main()
            self.assertEqual(failure.exception.code, 2)
            data = json.loads(report.read_text(encoding='utf-8'))
            self.assertEqual(data['classification'], 'diagnostic_unavailable')
            self.assertEqual(data['error_type'], 'JSONDecodeError')
            self.assertFalse(data['provenance_verified'])
            self.assertFalse(data['gameplay_parity_verified'])
            self.assertFalse(data['kaggle_started'])

    def test_cli_preserves_swf_mismatch_failure_without_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            swf, jar = root / 'game.swf', root / 'ffdec.jar'
            swf.write_bytes(b'changed SWF')
            jar.write_bytes(b'FFDec fixture')
            committed = root / 'committed.json'
            manifest = root / 'manifest.json'
            report = root / 'diagnostic.json'
            expected_swf = digest(b'original SWF')
            committed.write_text(json.dumps({'source': {
                'swf_sha256': expected_swf,
                'renderer_actionscript_path': 'export/scripts/frame_4346/DoAction_2.as',
                'renderer_actionscript_sha256': digest(b'original script'),
            }}), encoding='utf-8')
            manifest.write_text(json.dumps({'original': {'sha256': expected_swf},
                                            'files': []}), encoding='utf-8')
            argv = ['ffdec-drift', '--committed', str(committed),
                    '--manifest', str(manifest), '--swf', str(swf),
                    '--ffdec', str(jar), '--export-root', str(root / 'export'),
                    '--out', str(report)]
            with patch.object(sys, 'argv', argv), patch(
                    'subprocess.run', side_effect=AssertionError('no FFDec retry')
            ), redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as failure:
                    main()
            self.assertEqual(failure.exception.code, 2)
            data = json.loads(report.read_text(encoding='utf-8'))
            self.assertEqual(data['classification'], 'diagnostic_unavailable')
            self.assertIn('SWF provenance mismatch', data['error_message'])
            self.assertFalse(data['provenance_verified'])
            self.assertFalse(data['kaggle_started'])

if __name__ == '__main__':
    unittest.main()
