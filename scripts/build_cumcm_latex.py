#!/usr/bin/env python3
"""Build a CUMCM LaTeX paper with repeatable XeLaTeX passes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def executable_version(executable: str) -> str:
    try:
        result = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    lines = (result.stdout or result.stderr).splitlines()
    return lines[0].strip() if lines else "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("main_tex", type=Path, help="Main TeX file")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--xelatex", help="Explicit XeLaTeX executable")
    parser.add_argument("--passes", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=180, help="Timeout per pass in seconds")
    return parser.parse_args()


def sanitized_environment(executable: str) -> tuple[dict[str, str], list[str]]:
    environment = os.environ.copy()
    kept: list[str] = []
    dropped: list[str] = []
    for entry in environment.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        expanded = os.path.expandvars(entry.strip('"'))
        if Path(expanded).is_dir():
            kept.append(entry)
        else:
            dropped.append(entry)
    executable_path = Path(executable)
    if executable_path.is_file():
        parent = str(executable_path.resolve().parent)
        if all(Path(os.path.expandvars(item.strip('"'))).resolve() != Path(parent) for item in kept):
            kept.insert(0, parent)
    environment["PATH"] = os.pathsep.join(kept)
    return environment, dropped


def main() -> int:
    args = parse_args()
    main_tex = args.main_tex.expanduser().resolve()
    if not main_tex.is_file() or main_tex.suffix.lower() != ".tex":
        print(f"Main TeX file not found: {main_tex}", file=sys.stderr)
        return 2
    if args.passes < 1 or args.passes > 5:
        print("--passes must be between 1 and 5", file=sys.stderr)
        return 2

    executable = args.xelatex or shutil.which("xelatex")
    if not executable:
        print("XeLaTeX was not found. Install a TeX distribution or pass --xelatex.", file=sys.stderr)
        return 2

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-no-shell-escape",
        f"-output-directory={output_dir}",
        main_tex.name,
    ]
    environment, dropped_path_entries = sanitized_environment(executable)
    pass_records: list[dict[str, object]] = []

    for pass_number in range(1, args.passes + 1):
        try:
            result = subprocess.run(
                command,
                cwd=main_tex.parent,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=args.timeout,
            )
        except subprocess.TimeoutExpired as exc:
            print(f"XeLaTeX pass {pass_number} exceeded {args.timeout} seconds.", file=sys.stderr)
            if exc.stdout:
                print(str(exc.stdout)[-4000:], file=sys.stderr)
            return 2

        console_log = output_dir / f"{main_tex.stem}-pass-{pass_number}.console.txt"
        console_log.write_text((result.stdout or "") + (result.stderr or ""), encoding="utf-8")
        pass_records.append(
            {
                "pass": pass_number,
                "return_code": result.returncode,
                "console_log": console_log.name,
            }
        )
        if result.returncode != 0:
            tail = ((result.stdout or "") + (result.stderr or "")).splitlines()[-60:]
            print("\n".join(tail), file=sys.stderr)
            print(f"XeLaTeX pass {pass_number} failed. See {console_log}", file=sys.stderr)
            return 2


    pdf = output_dir / f"{main_tex.stem}.pdf"
    if not pdf.is_file() or pdf.stat().st_size == 0:
        print(f"XeLaTeX reported success but PDF is missing: {pdf}", file=sys.stderr)
        return 2

    manifest = {
        "schema_version": 1,
        "built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "main_tex": str(main_tex),
        "main_tex_sha256": sha256(main_tex),
        "xelatex": str(Path(executable).resolve()) if Path(executable).exists() else executable,
        "xelatex_version": executable_version(executable),
        "dropped_non_directory_path_entries": dropped_path_entries,
        "command": command,
        "passes": pass_records,
        "pdf": str(pdf),
        "pdf_sha256": sha256(pdf),
        "pdf_size_bytes": pdf.stat().st_size,
    }
    manifest_path = output_dir / f"{main_tex.stem}-build-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PDF: {pdf}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
