#!/usr/bin/env python3
"""Create a safe, evidence-gated mathematical-modeling workspace."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "2.0"


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_files(mode: str, question_count: int) -> dict[str, Any]:
    question_ids = [f"Q{i}" for i in range(1, question_count + 1)]
    created_at = datetime.now(timezone.utc).isoformat()
    questions = [
        {
            "id": question_id,
            "objective": "TODO",
            "inputs": [],
            "output_contract": "TODO",
            "dependencies": [],
            "decision_variables": [],
            "constraints": [],
            "units": {},
            "assumptions": [],
            "primary_metric": "TODO",
        }
        for question_id in question_ids
    ]
    decisions = [
        {
            "id": question_id,
            "baseline": "",
            "candidates": [],
            "comparison_criteria": [
                "assumption_fit",
                "data_fit",
                "interpretability",
                "runtime",
                "validation_burden",
            ],
            "feasibility_probe": {
                "status": "pending",
                "artifact_path": "",
                "finding": "",
            },
            "selected_method": "",
            "rejection_reasons": {},
            "validation_plan": "",
            "fallback": "",
            "user_decision": "pending",
        }
        for question_id in question_ids
    ]
    return {
        "audit/project-state.json": {
            "schema_version": SCHEMA_VERSION,
            "created_at": created_at,
            "mode": mode,
            "status": "initialized",
            "active_gate": "intake",
            "subquestions": question_ids,
            "stale_from": None,
            "notes": [],
        },
        "planning/problem-contract.json": {
            "schema_version": SCHEMA_VERSION,
            "title": "TODO",
            "decision_to_support": "TODO",
            "time_budget": "TODO",
            "deliverables": [],
            "global_assumptions": [],
            "data_sources": [],
            "subquestions": questions,
        },
        "planning/method-decision.json": {
            "schema_version": SCHEMA_VERSION,
            "questions": decisions,
        },
        "audit/reproducibility-manifest.json": {
            "schema_version": SCHEMA_VERSION,
            "run_mode": mode,
            "illustrative_only": mode == "demo",
            "executed": False,
            "completed_at": None,
            "command": "",
            "random_seeds": [],
            "environment": {
                "os": "",
                "language": "",
                "dependencies": {},
            },
            "inputs": [],
            "parameters": {},
            "source_files": [],
            "output_files": [],
            "notes": [],
        },
        "results/frozen-results.json": {
            "schema_version": SCHEMA_VERSION,
            "frozen": False,
            "version": "",
            "approved_by": "",
            "approved_at": None,
            "metrics": [],
            "validation_evidence": [],
            "limitations": [],
        },
    }


def initialize(root: Path, mode: str, question_count: int, force: bool) -> None:
    root = root.expanduser().resolve()
    if root == Path(root.anchor):
        raise SystemExit("Refusing to initialize directly in a filesystem root")
    structured_files = build_files(mode, question_count)
    text_files = {
        "planning/data-audit.csv": (
            "input_id,path,source,retrieval_date,unit,provenance_verified,"
            "missingness_checked,outliers_checked,leakage_checked,notes\n"
        ),
        "audit/claim-evidence-ledger.csv": (
            "claim_id,claim_text,scope,evidence_type,artifact_path,"
            "artifact_anchor,method_or_code,validation_status,limitations,status\n"
        ),
        "paper/main.md": (
            "# Modeling Report\n\n"
            "> DRAFT: replace all TODO markers and use only frozen results.\n\n"
            "## Abstract\n\nTODO\n\n"
            "## Problem and Assumptions\n\nTODO\n\n"
            "## Model\n\nTODO\n\n"
            "## Results and Validation\n\nTODO\n\n"
            "## Limitations\n\nTODO\n"
        ),
        "src/README.md": (
            "# Source Code\n\n"
            "Place executable analysis code here. Record the exact entry command "
            "in audit/reproducibility-manifest.json.\n"
        ),
    }
    relative_paths = list(structured_files) + list(text_files)
    collisions = [path for path in relative_paths if (root / path).exists()]
    if collisions and not force:
        joined = "\n  ".join(collisions)
        raise SystemExit(
            "Refusing to overwrite existing generated files. "
            "Use --force only after reviewing them:\n  " + joined
        )

    for directory in (
        "input",
        "planning",
        "src",
        "results/tables",
        "results/figures",
        "paper",
        "audit",
    ):
        (root / directory).mkdir(parents=True, exist_ok=True)

    for relative_path, value in structured_files.items():
        write_json(root / relative_path, value)
    for relative_path, value in text_files.items():
        (root / relative_path).write_text(value, encoding="utf-8")

    with (root / "planning/data-audit.csv").open(
        "a", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "D001",
                "input/TODO",
                "TODO",
                "TODO",
                "TODO",
                "false",
                "false",
                "false",
                "false",
                "Replace this row with a real input audit.",
            ]
        )

    print(f"Initialized evidence-gated modeling project: {root}")
    print(f"Mode: {mode}; sub-questions: {question_count}")
    print("Next: complete planning/problem-contract.json and the data audit.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize an evidence-gated mathematical-modeling project."
    )
    parser.add_argument("project_dir", type=Path)
    parser.add_argument(
        "--mode",
        choices=("formal", "demo", "blocked"),
        default="formal",
    )
    parser.add_argument("--questions", type=int, default=1)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite generated files after you have reviewed existing content.",
    )
    args = parser.parse_args()
    if not 1 <= args.questions <= 50:
        parser.error("--questions must be between 1 and 50")
    return args


def main() -> None:
    args = parse_args()
    initialize(args.project_dir, args.mode, args.questions, args.force)


if __name__ == "__main__":
    main()
