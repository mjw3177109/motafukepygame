"""Strict, dependency-free SWF header + tag inventory (FWS/CWS)."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import zlib
from collections import Counter
from pathlib import Path


def _bits(data: bytes, bit_offset: int, width: int, signed: bool = False) -> int:
    if width == 0:
        return 0
    if bit_offset + width > len(data) * 8:
        raise ValueError("truncated SWF RECT")
    number = 0
    for i in range(width):
        p = bit_offset + i
        number = (number << 1) | ((data[p // 8] >> (7 - p % 8)) & 1)
    if signed and number & (1 << (width - 1)):
        number -= 1 << width
    return number


def probe(raw: bytes) -> dict:
    if len(raw) < 9:
        raise ValueError("SWF too short")
    signature = raw[:3]
    if signature not in (b"FWS", b"CWS", b"ZWS"):
        raise ValueError("invalid SWF signature")
    version, declared_length = raw[3], struct.unpack_from("<I", raw, 4)[0]
    if declared_length < 12 or declared_length > 200_000_000:
        raise ValueError("implausible SWF declared length")
    if signature == b"ZWS":
        raise ValueError("ZWS/LZMA requires FFDec; do not guess compression layout")
    body = raw[8:] if signature == b"FWS" else zlib.decompress(raw[8:])
    if len(body) + 8 != declared_length:
        raise ValueError("SWF uncompressed size does not match header")
    n = _bits(body, 0, 5)
    if n == 0 or n > 31:
        raise ValueError("invalid SWF RECT bit width")
    p = 5
    edges = []
    for _ in range(4):
        edges.append(_bits(body, p, n, signed=True))
        p += n
    byte_offset = (p + 7) // 8
    if byte_offset + 4 > len(body):
        raise ValueError("truncated SWF frame metadata")
    fps_raw, frame_count = struct.unpack_from("<HH", body, byte_offset)
    tag_offset = byte_offset + 4
    counts = Counter()
    tags_parsed = 0
    end_seen = False
    while tag_offset + 2 <= len(body):
        tag_info = struct.unpack_from("<H", body, tag_offset)[0]
        tag_offset += 2
        tag_type, length = tag_info >> 6, tag_info & 63
        if length == 63:
            if tag_offset + 4 > len(body):
                raise ValueError("truncated SWF long tag header")
            length = struct.unpack_from("<I", body, tag_offset)[0]
            tag_offset += 4
        if tag_offset + length > len(body):
            raise ValueError("truncated SWF tag")
        counts[str(tag_type)] += 1
        tags_parsed += 1
        tag_offset += length
        if tag_type == 0:
            end_seen = True
            break
    if not end_seen:
        raise ValueError("no SWF End tag encountered")
    xmin, xmax, ymin, ymax = edges
    return {
        "signature": signature.decode("ascii"),
        "swf_version": version,
        "declared_uncompressed_bytes": declared_length,
        "source_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "stage_twips": {"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
        "stage_pixels": {"width": (xmax - xmin) / 20, "height": (ymax - ymin) / 20},
        "frame_rate": fps_raw / 256,
        "frame_count": frame_count,
        "tags_parsed": tags_parsed,
        "tag_counts": dict(sorted(counts.items(), key=lambda e: int(e[0]))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("swf", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = probe(args.swf.read_bytes())
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
