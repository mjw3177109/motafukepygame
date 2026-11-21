"""Casefold collision regressions for FFDec exports on case-sensitive runners.

These synthetic cases protect exact-path identity. They do not certify the eight
collision groups observed in the original game.swf artifact.
"""
import unittest

from tools.compare_ffdec_exports import compare


def manifest(entries):
    return {
        "original": {"sha256": "a" * 64},
        "exported_file_count": len(entries),
        "ffdec_commands": [{"exit_code": 0}],
        "files": [
            {"path": path, "size": size, "sha256": digest * 64}
            for path, size, digest in entries
        ],
    }


class CasefoldCollisionRegressionTests(unittest.TestCase):
    def test_eight_collision_groups_are_reported_without_collapsing_paths(self):
        entries = [
            (f"assets/{i}/Shape.svg", i + 1, "a")
            for i in range(8)
        ] + [
            (f"assets/{i}/shape.svg", i + 2, "b")
            for i in range(8)
        ]
        result = compare(manifest(entries), manifest(list(reversed(entries))))
        self.assertTrue(result["identical"])
        self.assertEqual(result["first_count"], 16)
        self.assertEqual(result["first_casefold_collisions"], [
            [f"assets/{i}/Shape.svg", f"assets/{i}/shape.svg"]
            for i in range(8)
        ])
        self.assertEqual(result["second_casefold_collisions"],
                         result["first_casefold_collisions"])

    def test_case_only_rename_and_changed_content_fail_closed(self):
        first = manifest([("A.svg", 3, "a"), ("a.svg", 4, "b")])
        changed = manifest([("A.svg", 3, "b"), ("a.svg", 4, "b")])
        renamed = manifest([("A.svg", 3, "a"), ("a.SVG", 4, "b")])
        changed_result = compare(first, changed)
        self.assertFalse(changed_result["identical"])
        self.assertEqual(changed_result["changed"], ["A.svg"])
        renamed_result = compare(first, renamed)
        self.assertFalse(renamed_result["identical"])
        self.assertEqual(renamed_result["only_first"], ["a.svg"])
        self.assertEqual(renamed_result["only_second"], ["a.SVG"])


if __name__ == "__main__":
    unittest.main()
