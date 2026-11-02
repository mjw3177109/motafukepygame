import struct
import unittest
import zlib

from tools.swf_probe import probe


def fake_swf(compressed=False):
    # RECT with nbits=1 and all coordinates zero, then pad to byte boundary.
    body = bytes([0b00001000, 0]) + struct.pack("<HH", 12 * 256, 1)
    body += struct.pack("<H", 0)  # End tag
    header = (b"CWS" if compressed else b"FWS") + bytes([7]) + struct.pack("<I", len(body) + 8)
    return header + (zlib.compress(body) if compressed else body)


class SWFProbeTests(unittest.TestCase):
    def test_fws(self):
        info = probe(fake_swf())
        self.assertEqual(info["frame_rate"], 12)
        self.assertEqual(info["frame_count"], 1)
        self.assertEqual(info["tag_counts"], {"0": 1})

    def test_cws(self):
        self.assertEqual(probe(fake_swf(True))["signature"], "CWS")

    def test_reject_bad_size(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            probe(fake_swf() + b"extra")

    def test_reject_bad_signature(self):
        with self.assertRaises(ValueError):
            probe(b"BAD" + fake_swf()[3:])


if __name__ == "__main__":
    unittest.main()
