"""Regression tests for arbitrary FFDec drift evidence summaries."""
import tempfile
import unittest
from pathlib import Path
from tools.inspect_ffdec_drift import summarize


class DriftSummaryTests(unittest.TestCase):
    def test_changed_and_one_sided(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a', Path(tmp) / 'b'
            a.mkdir()
            b.mkdir()
            (a / 'x.as').write_bytes(b'abc')
            (b / 'x.as').write_bytes(b'abZ')
            (a / 'left.as').write_bytes(b'L')
            (b / 'right.as').write_bytes(b'R')
            report = {'changed': ['x.as'], 'only_first': ['left.as'], 'only_second': ['right.as']}
            rows = summarize(report, a, b)['drift']
            self.assertEqual(rows[0]['first_difference_offset'], 2)
            self.assertIsNone(rows[1]['second'])
            self.assertIsNone(rows[2]['first'])
            self.assertFalse(rows[0]['actionrecord_semantics_verified'])

    def test_missing_changed_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a', Path(tmp) / 'b'
            a.mkdir()
            b.mkdir()
            (a / 'x.as').write_bytes(b'first')
            with self.assertRaisesRegex(ValueError, 'incomplete or contradictory'):
                summarize({'changed': ['x.as']}, a, b)

    def test_contradictory_one_sided_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a', Path(tmp) / 'b'
            a.mkdir()
            b.mkdir()
            (a / 'x.as').write_bytes(b'first')
            (b / 'x.as').write_bytes(b'second')
            with self.assertRaisesRegex(ValueError, 'incomplete or contradictory'):
                summarize({'only_first': ['x.as']}, a, b)
            with self.assertRaisesRegex(ValueError, 'incomplete or contradictory'):
                summarize({'only_second': ['x.as']}, a, b)

    def test_identical_changed_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a', Path(tmp) / 'b'
            a.mkdir()
            b.mkdir()
            (a / 'x.as').write_bytes(b'same')
            (b / 'x.as').write_bytes(b'same')
            with self.assertRaisesRegex(ValueError, 'incomplete or contradictory'):
                summarize({'changed': ['x.as']}, a, b)

    def test_duplicate_path_across_categories_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a', Path(tmp) / 'b'
            a.mkdir()
            b.mkdir()
            (a / 'x.as').write_bytes(b'first')
            (b / 'x.as').write_bytes(b'second')
            with self.assertRaisesRegex(ValueError, 'duplicate drift evidence path'):
                summarize({'changed': ['x.as'], 'only_first': ['x.as']}, a, b)

    def test_duplicate_path_within_category_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a', Path(tmp) / 'b'
            a.mkdir()
            b.mkdir()
            (a / 'x.as').write_bytes(b'first')
            (b / 'x.as').write_bytes(b'second')
            with self.assertRaisesRegex(ValueError, 'duplicate drift evidence path'):
                summarize({'changed': ['x.as', 'x.as']}, a, b)

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                summarize({'changed': ['../secret']}, Path(tmp), Path(tmp))

    def test_unknown_category_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'unknown drift report categories'):
                summarize({'changed': [], 'unexpected': ['ignored.as']}, Path(tmp), Path(tmp))

    def test_non_object_report_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'invalid drift report object'):
                summarize(['changed'], Path(tmp), Path(tmp))


if __name__ == '__main__':
    unittest.main()
