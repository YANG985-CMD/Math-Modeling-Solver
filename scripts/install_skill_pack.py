#!/usr/bin/env python3
"""Install the compatible root Skill and its three specialist Skills."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_FILES = ("SKILL.md", "LICENSE", "pyproject.toml")
CORE_DIRS = ("agents", "assets", "benchmarks", "references", "scripts")
SPECIALISTS = (
    "audit-modeling-evidence",
    "build-modeling-figures",
    "deliver-cumcm-paper",
)


def default_target() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    return (Path(codex_home).expanduser() if codex_home else Path.home() / ".codex") / "skills"


def copy_path(source: Path, destination: Path, *, dry_run: bool) -> None:
    if dry_run:
        print(f"would copy {source} -> {destination}")
        return
    if source.is_dir():
        shutil.copytree(
            source,
            destination,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
        )
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=default_target())
    parser.add_argument("--force", action="store_true", help="Allow existing destinations.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    destinations = [args.target / "math-modeling-solver", *(args.target / name for name in SPECIALISTS)]
    if not args.dry_run and not args.force:
        existing = [str(path) for path in destinations if path.exists()]
        if existing:
            parser.error("destination exists; pass --force to update: " + ", ".join(existing))

    core_destination = destinations[0]
    for relative in CORE_FILES:
        copy_path(ROOT / relative, core_destination / relative, dry_run=args.dry_run)
    for relative in CORE_DIRS:
        copy_path(ROOT / relative, core_destination / relative, dry_run=args.dry_run)
    for name, destination in zip(SPECIALISTS, destinations[1:]):
        copy_path(ROOT / name, destination, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"installed math-modeling-solver and {len(SPECIALISTS)} specialists under {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
