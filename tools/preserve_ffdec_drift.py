"""Preserve all differing FFDec exports, including files present on only one side."""
import argparse
import json
import shutil
from pathlib import Path, PurePosixPath


def preserve(report_path: Path, first: Path, second: Path, out: Path) -> int:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    categories = ("changed", "only_first", "only_second")
    for category in categories:
        paths = report.get(category, [] if category != "changed" else None)
        if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
            raise ValueError("invalid " + category + " paths")
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate " + category + " paths")
    if any(set(report[a]) & set(report[b]) for i, a in enumerate(categories)
           for b in categories[i + 1:] if a in report and b in report):
        raise ValueError("overlapping drift categories")
    roots = [first.resolve(strict=True), second.resolve(strict=True)]
    dest = out.resolve()
    if any(dest == root or dest.is_relative_to(root) or root.is_relative_to(dest) for root in roots):
        raise ValueError("output overlaps source tree")
    copies = []
    for category in categories:
        for path in report.get(category, []):
            pure = PurePosixPath(path)
            if (not path or "\\" in path or ":" in path or pure.is_absolute()
                    or any(part in ("", ".", "..") for part in path.split("/"))
                    or any(ord(char) < 32 or ord(char) == 127 for char in path)):
                raise ValueError("unsafe drift path: " + path)
            sides = (0, 1) if category == "changed" else ((0,) if category == "only_first" else (1,))
            for side in sides:
                root = roots[side]
                source = root.joinpath(*pure.parts)
                if (source.is_symlink() or not source.resolve().is_relative_to(root)
                        or not source.is_file()):
                    raise ValueError("missing or unsafe source: " + path)
                copies.append((side, pure, source))
    # Preflight all inputs before writing evidence, including destination symlinks.
    for side, pure, _ in copies:
        target = dest / ("first" if side == 0 else "second") / pure
        if any(part.is_symlink() for part in (target, *target.parents) if part != dest.parent):
            raise ValueError("unsafe target: " + str(target))
    for side, pure, source in copies:
        target = dest / ("first" if side == 0 else "second") / pure
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return sum(len(report.get(category, [])) for category in categories)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("report", "first", "second", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print("Preserved drift paths:", preserve(args.report, args.first, args.second, args.out))


if __name__ == "__main__":
    main()
