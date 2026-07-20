#!/usr/bin/env python3
"""Create the optional claim/result/run/figure evidence registry bundle."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REGISTRIES: dict[str, tuple[str, ...]] = {
    "results/result-registry.csv": (
        "result_id",
        "question_id",
        "metric_name",
        "value",
        "unit",
        "direction",
        "artifact_path",
        "artifact_sha256",
        "run_id",
        "validation_status",
        "result_status",
        "supersedes",
        "human_approved",
        "notes",
    ),
    "audit/poc-registry.csv": (
        "poc_id",
        "question_id",
        "input_path",
        "command",
        "output_path",
        "run_id",
        "status",
        "failure_reason",
        "human_approved",
        "notes",
    ),
    "audit/run-record.csv": (
        "run_id",
        "question_id",
        "command",
        "working_directory",
        "input_paths",
        "output_paths",
        "parameters",
        "seeds",
        "software_versions",
        "started_at",
        "finished_at",
        "exit_code",
        "status",
        "log_path",
    ),
    "audit/figure-evidence.csv": (
        "figure_id",
        "claim_id",
        "result_ids",
        "source_data_path",
        "generator_path",
        "command",
        "output_paths",
        "caption",
        "visual_check_status",
        "final_size_check",
        "human_approved",
        "status",
        "notes",
    ),
    "audit/numerical-diagnostics.csv": (
        "diagnostic_id",
        "result_id",
        "diagnostic_type",
        "observed_value",
        "threshold",
        "direction",
        "artifact_path",
        "status",
        "notes",
    ),
    "audit/review-pass-items.csv": (
        "item_id",
        "file_path",
        "locator",
        "check_type",
        "observed_value",
        "expected_condition",
        "evidence_path",
        "reviewer",
        "status",
        "notes",
    ),
    "audit/consistency-audit.csv": (
        "item_id",
        "source_type",
        "source_path",
        "source_locator",
        "target_type",
        "target_path",
        "target_locator",
        "field",
        "source_value",
        "target_value",
        "status",
        "notes",
    ),
}


def initialize(root: Path, *, force: bool = False) -> list[Path]:
    root = root.expanduser().resolve()
    if root == Path(root.anchor):
        raise SystemExit("Refusing to initialize directly in a filesystem root")
    collisions = [relative for relative in REGISTRIES if (root / relative).exists()]
    if collisions and not force:
        raise SystemExit(
            "Refusing to overwrite existing registries; pass --force after review: "
            + ", ".join(collisions)
        )
    created: list[Path] = []
    for relative, fields in REGISTRIES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow(fields)
        created.append(path)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    created = initialize(args.project_dir, force=args.force)
    print(f"created {len(created)} evidence registries under {args.project_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
