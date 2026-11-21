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

    def test_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                summarize({'changed': ['../secret']}, Path(tmp), Path(tmp))


if __name__ == '__main__':
    unittest.main()
