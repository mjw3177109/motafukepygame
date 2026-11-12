"""Regression checks for FFDec inventory comparison."""
import unittest
from tools.compare_ffdec_exports import compare


def manifest(items, source="a" * 64):
    return {"original": {"sha256": source}, "exported_file_count": len(items),
            "ffdec_commands": [{"exit_code": 0}],
            "files": [{"path": p, "size": n, "sha256": h * 64} for p, n, h in items]}


class CompareFFDecTests(unittest.TestCase):
    def test_order_and_case_distinct_paths(self):
        entries = [("A.svg", 2, "a"), ("a.svg", 3, "b")]
        self.assertTrue(compare(manifest(entries), manifest(entries[::-1]))["identical"])

    def test_missing_added_and_changed(self):
        result = compare(manifest([("a", 2, "a"), ("b", 3, "b")]),
                         manifest([("a", 4, "a"), ("c", 3, "b")]))
        self.assertEqual(result["only_first"], ["b"])
        self.assertEqual(result["only_second"], ["c"])
        self.assertEqual(result["changed"], ["a"])
        self.assertFalse(result["identical"])

    def test_source_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            compare(manifest([("a", 2, "a")]), manifest([("a", 2, "a")], "b" * 64))

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            compare(manifest([("a", 2, "a"), ("a", 2, "a")]), manifest([("a", 2, "a")]))

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            compare(manifest([]), manifest([("a", 2, "a")]))

    def test_invalid_manifest_entries_rejected(self):
        valid = manifest([("safe/file.svg", 2, "a")])
        for path in ("../escape.svg", "/absolute.svg", "a//b.svg", "a/./b.svg", "a\\b.svg", ""):
            with self.subTest(path=path):
                bad = manifest([("safe/file.svg", 2, "a")])
                bad["files"][0]["path"] = path
                with self.assertRaises(ValueError):
                    compare(bad, valid)
        for size in (True, -1, "2"):
            with self.subTest(size=size):
                bad = manifest([("safe/file.svg", 2, "a")])
                bad["files"][0]["size"] = size
                with self.assertRaises(ValueError):
                    compare(bad, valid)
        for digest in ("z" * 64, "a" * 63, 123):
            with self.subTest(digest=digest):
                bad = manifest([("safe/file.svg", 2, "a")])
                bad["files"][0]["sha256"] = digest
                with self.assertRaises(ValueError):
                    compare(bad, valid)

    def test_failed_ffdec_rejected(self):
        bad = manifest([("a", 2, "a")])
        bad["ffdec_commands"][0]["exit_code"] = 1
        with self.assertRaises(ValueError):
            compare(bad, manifest([("a", 2, "a")]))
