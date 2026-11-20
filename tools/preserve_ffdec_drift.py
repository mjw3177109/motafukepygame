"""Preserve both sides of every changed FFDec export without weakening fail-closed audit."""
import argparse
import json
import shutil
from pathlib import Path, PurePosixPath


def preserve(report_path: Path, first: Path, second: Path, out: Path) -> int:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    changed = report.get("changed")
    if not isinstance(changed, list) or any(not isinstance(p, str) for p in changed):
        raise ValueError("invalid changed paths")
    if len(changed) != len(set(changed)):
        raise ValueError("duplicate changed paths")
    roots = [first.resolve(strict=True), second.resolve(strict=True)]
    dest = out.resolve()
    if any(dest == root or dest.is_relative_to(root) or root.is_relative_to(dest) for root in roots):
        raise ValueError("output overlaps source tree")
    pairs = []
    for path in changed:
        pure = PurePosixPath(path)
        if (not path or "\\" in path or ":" in path or pure.is_absolute()
                or any(part in ("", ".", "..") for part in path.split("/"))):
            raise ValueError("unsafe changed path: " + path)
        sources = []
        for root in roots:
            source = root.joinpath(*pure.parts)
            if source.is_symlink() or not source.resolve().is_relative_to(root) or not source.is_file():
                raise ValueError("missing or unsafe source: " + path)
            sources.append(source)
        pairs.append((pure, sources))
    for pure, sources in pairs:
        for label, source in zip(("first", "second"), sources):
            target = dest / label / pure
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink():
                raise ValueError("unsafe target: " + str(target))
            shutil.copyfile(source, target)
    return len(pairs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("report", "first", "second", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print("Preserved drift paths:", preserve(args.report, args.first, args.second, args.out))


if __name__ == "__main__":
    main()
