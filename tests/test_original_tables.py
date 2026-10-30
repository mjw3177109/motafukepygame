"""Fail-closed tests for extraction of original ActionScript static data."""
import unittest

from tools.extract_original_tables import parse_tables


SWF_HASH = "0" * 64


def fixture():
    chunks = []
    for floor in range(27):
        chunks.append(f"mt_line_{floor:02d} = new Array(11);")
        for row in range(11):
            chunks.append(f"mt_line_{floor:02d}[{row}] = new Array(" + ",".join(str(floor + row + col) for col in range(11)) + ");")
    chunks.extend(f'boss_man[{i}] = new Array({i},2,3,4,5,"怪物{i}");' for i in range(33))
    chunks.extend(f"Base_{name} = {i};" for i, name in enumerate(("life", "hp", "gong", "fang", "money", "yellow", "blue", "red", "mp")))
    return "\n".join(chunks).encode("utf-8")


class OriginalTablesTests(unittest.TestCase):
    def test_complete_untransposed_tables(self):
        result = parse_tables(fixture(), swf_sha256=SWF_HASH)
        self.assertEqual(len(result["floors"]), 27)
        self.assertEqual(result["floors"]["02"][3][4], 9)
        self.assertEqual(result["monsters"]["32"], [32, 2, 3, 4, 5, "怪物32"])
        self.assertEqual(result["base_stats"]["hp"], 1)

    def test_missing_row_rejected(self):
        source = fixture().replace(b"mt_line_01[3] = new Array(", b"ignored_01[3] = new Array(")
        with self.assertRaisesRegex(ValueError, "missing floor rows"):
            parse_tables(source, swf_sha256=SWF_HASH)

    def test_duplicate_monster_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate monster"):
            parse_tables(fixture() + b'\nboss_man[0] = new Array(1,2,3,4,5,"X");', swf_sha256=SWF_HASH)

    def test_missing_base_stat_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete original base"):
            parse_tables(fixture().replace(b"Base_hp = 1;", b""), swf_sha256=SWF_HASH)

    def test_invalid_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA256"):
            parse_tables(fixture(), swf_sha256="unknown")


if __name__ == "__main__":
    unittest.main()
