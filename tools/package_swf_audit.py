"""Losslessly package case-sensitive FFDec exports for GitHub Actions artifacts.

GitHub's upload-artifact treats artifact paths case-insensitively. Some FFDec
ActionScript exports differ only by filename case, so uploading the directory
can silently replace evidence. Keep the exact files inside a single tar.gz.
This is a preservation check, not a visual or gameplay parity assertion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
from collections import defaultdict
from pathlib import Path, PurePosixPath

HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def _valid_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(p not in ("", ".", "..") for p in value.split("/"))


def _digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def package_exports(manifest: dict, export_root: Path, archive_path: Path) -> dict:
    """Validate manifest against disk, archive, and verify exact member bytes."""
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("missing FFDec files inventory")
    expected: dict[str, tuple[int, str]] = {}
    for item in manifest["files"]:
        if (not isinstance(item, dict) or not _valid_path(item.get("path")) or
                type(item.get("size")) is not int or item["size"] < 0 or
                not isinstance(item.get("sha256"), str) or not HEX64.fullmatch(item["sha256"])):
            raise ValueError("invalid FFDec manifest file entry")
        name = item["path"]
        if name in expected:
            raise ValueError(f"duplicate FFDec manifest path: {name}")
        expected[name] = (item["size"], item["sha256"])
    if not expected:
        raise ValueError("FFDec export inventory is empty")
    root = export_root.resolve()
    if not root.is_dir():
        raise ValueError("FFDec export root missing")
    found = {}
    for target in root.rglob("*"):
        if target.is_symlink():
            raise ValueError("symlink not allowed in FFDec export")
        if not target.is_file():
            continue
        name = target.relative_to(root).as_posix()
        if not _valid_path(name) or name not in expected:
            raise ValueError(f"unlisted FFDec export: {name}")
        data = target.read_bytes()
        found[name] = (len(data), _digest(data))
        if found[name] != expected[name]:
            raise ValueError(f"FFDec export differs from manifest: {name}")
    if set(found) != set(expected):
        raise ValueError(f"missing FFDec exports: {sorted(set(expected) - set(found))[:5]}")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if archive_path.resolve().is_relative_to(root):
        raise ValueError("archive must be outside export root")
    with tarfile.open(archive_path, mode="w:gz") as archive:
        for name in sorted(expected):
            archive.add(root / name, arcname="export/" + name, recursive=False)
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        actual = {}
        for member in members:
            if not member.isfile() or not member.name.startswith("export/"):
                raise ValueError("unexpected archive member")
            name = member.name[len("export/"):]
            if not _valid_path(name) or name in actual or name not in expected:
                raise ValueError(f"invalid or duplicate archive member: {name}")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"unreadable archive member: {name}")
            data = stream.read()
            actual[name] = (len(data), _digest(data))
            if actual[name] != expected[name]:
                raise ValueError(f"archive bytes differ from FFDec manifest: {name}")
        if set(actual) != set(expected):
            raise ValueError("archive member list differs from FFDec manifest")
    folded = defaultdict(list)
    for name in expected:
        folded[name.casefold()].append(name)
    collisions = [sorted(group) for group in folded.values() if len(group) > 1]
    return {
        "schema_version": 1,
        "source_swf_sha256": manifest.get("original", {}).get("sha256"),
        "file_count": len(expected),
        "archive_sha256": _digest(archive_path.read_bytes()),
        "casefold_collision_groups": sorted(collisions),
        "archive_verified_against_manifest": True,
        "visual_parity_verified": False,
        "gameplay_parity_verified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--export-root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = package_exports(json.loads(args.manifest.read_text(encoding="utf-8")), args.export_root, args.archive)
    except (ValueError, OSError, tarfile.TarError, json.JSONDecodeError) as error:
        parser.exit(2, f"FFDec archive verification FAILED: {error}\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PASS: preserved {report['file_count']} exact FFDec exports in verified archive; "
          f"casefold collision groups: {len(report['casefold_collision_groups'])}; parity NOT VERIFIED")


if __name__ == "__main__":
    main()
