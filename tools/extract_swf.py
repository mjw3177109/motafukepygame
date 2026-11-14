"""Export auditable data from the actual SWF using the repository's FFDec."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from swf_probe import probe


def run_ffdec(jar: Path, args: list[str], logfile: Path, timeout: int = 480) -> dict:
    command = ["java", "-Xmx2g", "-Djava.awt.headless=true", "-jar", str(jar), "-cli", *args]
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        output = result.stdout + "\n" + result.stderr
        code = result.returncode
    except subprocess.TimeoutExpired as exc:
        output = str(exc)
        code = 124
    logfile.parent.mkdir(parents=True, exist_ok=True)
    logfile.write_text(output, encoding="utf-8", errors="replace")
    return {"argv": args, "exit_code": code, "log": str(logfile)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--swf", type=Path, default=Path("game.swf"))
    parser.add_argument("--ffdec", type=Path, default=Path("FFDec/ffdec.jar"))
    parser.add_argument("--out", type=Path, default=Path(".swf_audit"))
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    swf, jar, out = args.swf.resolve(), args.ffdec.resolve(), args.out.resolve()
    if not swf.is_file() or not jar.is_file():
        parser.error("original SWF and FFDec jar must both exist")
    out.mkdir(parents=True, exist_ok=True)
    metadata = probe(swf.read_bytes())
    (out / "swf_header.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    # SWF header is parsed by swf_probe; this FFDec build rejects -header.
    tasks = [
        ("tags", ["-dumpSWF", str(swf)]),
    ]
    if not args.metadata_only:
        tasks.append(("export", ["-onerror", "ignore", "-export",
                                 "script,image,shape,sound,text,button,font,binaryData",
                                 str(out / "export"), str(swf)]))
    runs = [run_ffdec(jar, argv, out / ("ffdec_" + title + ".log")) for title, argv in tasks]
    inventory = []
    export = out / "export"
    if export.exists():
        for file in sorted(x for x in export.rglob("*") if x.is_file()):
            blob = file.read_bytes()
            inventory.append({"path": file.relative_to(export).as_posix(),
                              "size": len(blob), "sha256": hashlib.sha256(blob).hexdigest()})
    report = {"original": metadata, "ffdec_commands": runs,
              "exported_file_count": len(inventory),
              "files": inventory, "parity_verified": False}
    (out / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"source_sha256": metadata["sha256"],
                      "exports": len(inventory), "commands": runs}, ensure_ascii=False, indent=2))
    if any(r["exit_code"] != 0 for r in runs):
        sys.exit("One or more FFDec commands failed; see log artifact")
    if not args.metadata_only and not inventory:
        sys.exit("FFDec exported zero files; original game is not yet inspected")


if __name__ == "__main__":
    main()
