"""Regression for eight actual FFDec casefold path collisions.

Source: SWF Original Audit run 43906380877, extract job 133436224961,
2026-11-16 16:20:57 UTC, ffdec_repeat_comparison JSON log.
Path evidence only; does not establish Flash runtime parity.
"""
import unittest

from tools.compare_ffdec_exports import compare


REAL_COLLISIONS = [
    ("715", "J"),
    ("718", "J"),
    ("856", "A"),
    ("856", "J"),
    ("856", "L"),
    ("856", "Q"),
    ("856", "R"),
    ("856", "S"),
]


def manifest(paths):
    return {
        "original": {"sha256": "a" * 64},
        "exported_file_count": len(paths),
        "ffdec_commands": [{"exit_code": 0}],
        "files": [
            {"path": path, "size": i + 1, "sha256": f"{i + 1:064x}"}
            for i, path in enumerate(paths)
        ],
    }


class RealCasefoldPathTests(unittest.TestCase):
    def test_observed_casefold_groups_preserve_exact_case(self):
        expected = [
            [
                f"scripts/DefineButton2_{sprite}/BUTTONCONDACTION on(keyPress {key}).as",
                f"scripts/DefineButton2_{sprite}/BUTTONCONDACTION on(keyPress {key.lower()}).as",
            ]
            for sprite, key in REAL_COLLISIONS
        ]
        paths = [path for group in expected for path in group]
        first = manifest(paths)
        second = manifest(list(reversed(paths)))
        second["files"] = list(reversed(first["files"]))
        result = compare(first, second)
        self.assertTrue(result["identical"])
        self.assertEqual(result["first_count"], 16)
        self.assertEqual(result["first_casefold_collisions"], expected)
        self.assertEqual(result["second_casefold_collisions"], expected)

    def test_observed_upper_lower_action_files_are_not_interchangeable(self):
        upper = "scripts/DefineButton2_856/BUTTONCONDACTION on(keyPress A).as"
        lower = "scripts/DefineButton2_856/BUTTONCONDACTION on(keyPress a).as"
        baseline = manifest([upper, lower])
        changed = manifest([upper, lower])
        changed["files"][1]["sha256"] = "f" * 64
        result = compare(baseline, changed)
        self.assertFalse(result["identical"])
        self.assertEqual(result["changed"], [lower])


if __name__ == "__main__":
    unittest.main()
