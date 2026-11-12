"""Fail-closed comparison of two independently exported FFDec inventories."""
import argparse
import json
import re
from pathlib import Path


def compare(first, second):
    def inventory(report):
        files = report.get("files")
        if not isinstance(files, list) or not files:
            raise ValueError("missing export inventory")
        if report.get("exported_file_count") != len(files):
            raise ValueError("export count mismatch")
        commands = report.get("ffdec_commands")
        if not commands or any(c.get("exit_code") != 0 for c in commands):
            raise ValueError("FFDec command missing or failed")
        found = {}
        for entry in files:
            path, size, digest = entry["path"], entry["size"], entry["sha256"]
            if path in found:
                raise ValueError("duplicate export path: " + path)
            if (not isinstance(path, str) or not path or path.startswith("/") or chr(92) in path
                    or any(part in ("", ".", "..") for part in path.split("/"))
                    or type(size) is not int or size < 0
                    or not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None):
                raise ValueError("invalid export entry: " + repr(path))
            found[path] = (size, digest)
        return found

    source = first.get("original", {}).get("sha256")
    if not isinstance(source, str) or re.fullmatch(r"[0-9a-fA-F]{64}", source) is None or source != second.get("original", {}).get("sha256"):
        raise ValueError("SWF source hash mismatch")
    a, b = inventory(first), inventory(second)
    missing = sorted(a.keys() - b.keys())
    added = sorted(b.keys() - a.keys())
    changed = sorted(k for k in a.keys() & b.keys() if a[k] != b[k])
    return {"source_sha256": source, "first_count": len(a), "second_count": len(b),
            "only_first": missing, "only_second": added, "changed": changed,
            "identical": not (missing or added or changed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = compare(json.loads(args.first.read_text(encoding="utf-8")),
                         json.loads(args.second.read_text(encoding="utf-8")))
    except (ValueError, KeyError, TypeError) as exc:
        parser.exit(2, "Invalid FFDec comparison: " + str(exc) + "\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    if not result["identical"]:
        parser.exit(1, "FFDec export mismatch\n")


if __name__ == "__main__":
    main()
