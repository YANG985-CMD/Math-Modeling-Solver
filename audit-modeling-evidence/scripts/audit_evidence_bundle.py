#!/usr/bin/env python3
"""Audit cross-links and freeze readiness of an evidence registry bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


REGISTRY_SCHEMAS: dict[str, tuple[str, ...]] = {
    "results/result-registry.csv": (
        "result_id", "question_id", "metric_name", "value", "unit", "direction",
        "artifact_path", "artifact_sha256", "run_id", "validation_status",
        "result_status", "supersedes", "human_approved", "notes",
    ),
    "audit/poc-registry.csv": (
        "poc_id", "question_id", "input_path", "command", "output_path", "run_id",
        "status", "failure_reason", "human_approved", "notes",
    ),
    "audit/run-record.csv": (
        "run_id", "question_id", "command", "working_directory", "input_paths",
        "output_paths", "parameters", "seeds", "software_versions", "started_at",
        "finished_at", "exit_code", "status", "log_path",
    ),
    "audit/figure-evidence.csv": (
        "figure_id", "claim_id", "result_ids", "source_data_path", "generator_path",
        "command", "output_paths", "caption", "visual_check_status",
        "final_size_check", "human_approved", "status", "notes",
    ),
    "audit/numerical-diagnostics.csv": (
        "diagnostic_id", "result_id", "diagnostic_type", "observed_value",
        "threshold", "direction", "artifact_path", "status", "notes",
    ),
    "audit/review-pass-items.csv": (
        "item_id", "file_path", "locator", "check_type", "observed_value",
        "expected_condition", "evidence_path", "reviewer", "status", "notes",
    ),
    "audit/consistency-audit.csv": (
        "item_id", "source_type", "source_path", "source_locator", "target_type",
        "target_path", "target_locator", "field", "source_value", "target_value",
        "status", "notes",
    ),
}


def _read_csv(root: Path, relative: str, issues: list[str]) -> list[dict[str, str]]:
    path = root / relative
    if not path.is_file():
        issues.append(f"missing registry: {relative}")
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = tuple(reader.fieldnames or ())
            expected = REGISTRY_SCHEMAS[relative]
            missing = [field for field in expected if field not in fields]
            if missing:
                issues.append(f"{relative} missing columns: {', '.join(missing)}")
            return [dict(row) for row in reader]
    except (OSError, csv.Error) as exc:
        issues.append(f"cannot read {relative}: {exc}")
        return []


def _split_paths(value: str) -> list[str]:
    return [part.strip() for part in value.replace(";", "|").split("|") if part.strip()]


def _exists(root: Path, relative: str) -> bool:
    return bool(relative) and (root / relative).is_file()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(root: Path, *, require_review_items: int = 0) -> dict[str, Any]:
    root = root.expanduser().resolve()
    issues: list[str] = []
    rows = {
        relative: _read_csv(root, relative, issues)
        for relative in REGISTRY_SCHEMAS
    }
    results = {row.get("result_id", ""): row for row in rows["results/result-registry.csv"]}
    runs = {row.get("run_id", ""): row for row in rows["audit/run-record.csv"]}
    figures = rows["audit/figure-evidence.csv"]

    for result_id, row in results.items():
        if not result_id:
            issues.append("result registry contains a row without result_id")
            continue
        status = row.get("result_status", "")
        if status in {"paper_ready", "frozen", "manuscript"}:
            artifact = row.get("artifact_path", "")
            if not _exists(root, artifact):
                issues.append(f"result {result_id} artifact is missing: {artifact}")
            digest = row.get("artifact_sha256", "")
            if not digest:
                issues.append(f"result {result_id} has no artifact_sha256")
            elif _exists(root, artifact) and _sha256(root / artifact) != digest:
                issues.append(f"result {result_id} artifact hash does not match")
            run_id = row.get("run_id", "")
            run = runs.get(run_id)
            if not run or run.get("status") != "passed" or run.get("exit_code") not in {"", "0", "0.0"}:
                issues.append(f"result {result_id} does not link to a passed run")
            if row.get("validation_status") != "passed":
                issues.append(f"result {result_id} is not independently validated")
            if row.get("human_approved", "").lower() != "true":
                issues.append(f"result {result_id} lacks human approval")

    for row in rows["audit/poc-registry.csv"]:
        poc_id = row.get("poc_id", "unknown")
        if row.get("status") == "passed":
            if not _exists(root, row.get("input_path", "")):
                issues.append(f"PoC {poc_id} input is missing")
            if not _exists(root, row.get("output_path", "")):
                issues.append(f"PoC {poc_id} output is missing")
            if row.get("run_id", "") not in runs:
                issues.append(f"PoC {poc_id} does not link to a run")
        elif row.get("status") == "failed" and not row.get("failure_reason", "").strip():
            issues.append(f"PoC {poc_id} failed without a failure_reason")

    for row in figures:
        figure_id = row.get("figure_id", "unknown")
        if row.get("status") in {"paper_ready", "frozen", "manuscript"}:
            for field in ("source_data_path", "generator_path", "command", "caption"):
                if not row.get(field, "").strip():
                    issues.append(f"figure {figure_id} is missing {field}")
            for path in _split_paths(row.get("output_paths", "")):
                if not _exists(root, path):
                    issues.append(f"figure {figure_id} output is missing: {path}")
            if not _exists(root, row.get("source_data_path", "")):
                issues.append(f"figure {figure_id} source data is missing")
            if not _exists(root, row.get("generator_path", "")):
                issues.append(f"figure {figure_id} generator is missing")
            if row.get("visual_check_status") != "passed":
                issues.append(f"figure {figure_id} has not passed visual QA")
            if row.get("final_size_check") != "passed":
                issues.append(f"figure {figure_id} has not passed final-size QA")
            if row.get("human_approved", "").lower() != "true":
                issues.append(f"figure {figure_id} lacks human approval")

    review_items = rows["audit/review-pass-items.csv"]
    concrete = 0
    for row in review_items:
        item_id = row.get("item_id", "unknown")
        if row.get("status") == "passed":
            concrete += 1
            for field in ("file_path", "locator", "observed_value", "expected_condition", "evidence_path"):
                if not row.get(field, "").strip():
                    issues.append(f"review item {item_id} is missing {field}")
            if not _exists(root, row.get("file_path", "")):
                issues.append(f"review item {item_id} file is missing")
            if not _exists(root, row.get("evidence_path", "")):
                issues.append(f"review item {item_id} evidence is missing")
    if concrete < require_review_items:
        issues.append(f"review pass items: {concrete} passed, need {require_review_items}")

    for row in rows["audit/consistency-audit.csv"]:
        if row.get("status") == "passed" and row.get("source_value") != row.get("target_value"):
            issues.append(f"consistency item {row.get('item_id', 'unknown')} values differ")

    return {
        "project": str(root),
        "status": "passed" if not issues else "failed",
        "issues": issues,
        "counts": {key: len(value) for key, value in rows.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--require-review-items", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit(args.project_dir, require_review_items=args.require_review_items)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
