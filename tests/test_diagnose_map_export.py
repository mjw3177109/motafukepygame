import hashlib
import unittest
from tools.diagnose_map_export import inspect

class MapExportDiagnosticsTests(unittest.TestCase):
    def test_partial_export_is_not_approved(self):
        data = b''.join(f'mt_line_{i:02d} = new Array(11);\n'.encode() for i in range(12))
        report = inspect(data, hashlib.sha256(data).hexdigest())
        self.assertEqual(report['missing_floors'], list(range(12, 27)))
        self.assertFalse(report['gameplay_parity_verified'])
        self.assertFalse(report['provenance_verified'])
    def test_complete_declarations_report_no_missing(self):
        data = b''.join(f'mt_line_{i:02d} = new Array(11);\n'.encode() for i in range(27))
        self.assertEqual(inspect(data, hashlib.sha256(data).hexdigest())['missing_floors'], [])
    def test_wrong_anchor_is_reported(self):
        report = inspect(b'mt_line_00 = new Array(11);\n', '0'*64)
        self.assertFalse(report['anchor_matches'])
    def test_rejects_invalid_anchor(self):
        with self.assertRaises(ValueError):
            inspect(b'', 'abc')

    def test_duplicate_floor_with_different_array_lengths_is_rejected(self):
        data = b''.join(f'mt_line_{i:02d} = new Array(11);\n'.encode() for i in range(27))
        data += b'mt_line_06 = new Array(12);\n'
        report = inspect(data, hashlib.sha256(data).hexdigest())
        self.assertEqual(report['missing_floors'], [])
        self.assertEqual(report['duplicate_floors'], [6])
        self.assertFalse(report['gameplay_parity_verified'])

    def test_duplicate_floor_with_same_array_length_is_rejected(self):
        data = b'mt_line_00 = new Array(11);\nmt_line_00 = new Array(11);\n'
        report = inspect(data, hashlib.sha256(data).hexdigest())
        self.assertEqual(report['duplicate_floors'], [0])

    def test_unexpected_floor_is_not_silently_accepted(self):
        data = b''.join(f'mt_line_{i:02d} = new Array(11);\n'.encode() for i in range(28))
        report = inspect(data, hashlib.sha256(data).hexdigest())
        self.assertEqual(report['missing_floors'], [])
        self.assertEqual(report['unexpected_floors'], [27])
        self.assertFalse(report['gameplay_parity_verified'])
