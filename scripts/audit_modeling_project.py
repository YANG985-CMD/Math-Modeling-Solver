#!/usr/bin/env python3
"""Audit evidence gates in a math-modeling project."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


@dataclass
class GateResult:
    gate: str
    title: str
    status: str
    issues: list[str]


def load_json(root: Path, relative_path: str, issues: list[str]) -> dict[str, Any]:
    path = root / relative_path
    if not path.is_file():
        issues.append(f"Missing {relative_path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"Cannot parse {relative_path}: {exc}")
        return {}
    if not isinstance(value, dict):
        issues.append(f"{relative_path} must contain a JSON object")
        return {}
    return value


def has_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return not value.strip() or "TODO" in value.upper()
    return False


def relative_file_exists(root: Path, value: Any) -> bool:
    if not isinstance(value, str) or has_placeholder(value):
        return False
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return candidate.is_file()


def audit_intake(root: Path) -> list[str]:
    issues: list[str] = []
    state = load_json(root, "audit/project-state.json", issues)
    contract = load_json(root, "planning/problem-contract.json", issues)
    mode = state.get("mode")
    if mode not in {"formal", "demo", "blocked"}:
        issues.append("Project mode must be formal, demo, or blocked")
    for field in ("title", "decision_to_support", "time_budget"):
        if has_placeholder(contract.get(field)):
            issues.append(f"Problem contract field is incomplete: {field}")
    if not contract.get("deliverables"):
        issues.append("Problem contract has no deliverables")
    questions = contract.get("subquestions")
    if not isinstance(questions, list) or not questions:
        issues.append("Problem contract has no sub-questions")
    else:
        for question in questions:
            question_id = question.get("id", "unknown")
            for field in ("objective", "output_contract", "primary_metric"):
                if has_placeholder(question.get(field)):
                    issues.append(f"{question_id} is incomplete: {field}")

    audit_path = root / "planning/data-audit.csv"
    rows: list[dict[str, str]] = []
    if not audit_path.is_file():
        issues.append("Missing planning/data-audit.csv")
    else:
        try:
            with audit_path.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
        except OSError as exc:
            issues.append(f"Cannot read data audit: {exc}")
    if not rows:
        issues.append("Data audit has no input rows")
    for row in rows:
        input_id = row.get("input_id") or "unknown"
        for field in ("path", "source", "retrieval_date", "unit"):
            if has_placeholder(row.get(field)):
                issues.append(f"Data audit {input_id} is incomplete: {field}")
        if mode == "formal" and row.get("provenance_verified", "").lower() != "true":
            issues.append(f"Formal input {input_id} has unverified provenance")
        if not relative_file_exists(root, row.get("path")):
            issues.append(f"Input file is missing or outside project: {row.get('path')}")
        for check in ("missingness_checked", "outliers_checked", "leakage_checked"):
            if row.get(check, "").lower() != "true":
                issues.append(f"Data audit {input_id} has not passed {check}")
    return issues


def audit_method(root: Path) -> list[str]:
    issues: list[str] = []
    decisions = load_json(root, "planning/method-decision.json", issues)
    questions = decisions.get("questions")
    if not isinstance(questions, list) or not questions:
        return issues + ["Method decision has no sub-questions"]
    for question in questions:
        question_id = question.get("id", "unknown")
        if has_placeholder(question.get("baseline")):
            issues.append(f"{question_id} has no baseline")
        candidates = question.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            issues.append(f"{question_id} has no candidate comparison")
        if has_placeholder(question.get("selected_method")):
            issues.append(f"{question_id} has no selected method")
        if has_placeholder(question.get("validation_plan")):
            issues.append(f"{question_id} has no validation plan")
        probe = question.get("feasibility_probe") or {}
        if probe.get("status") != "passed":
            issues.append(f"{question_id} feasibility probe has not passed")
        if not relative_file_exists(root, probe.get("artifact_path")):
            issues.append(f"{question_id} feasibility evidence is missing")
        if question.get("user_decision") != "approved":
            issues.append(f"{question_id} method decision is not approved")
    return issues


def audit_computation(root: Path) -> list[str]:
    issues: list[str] = []
    manifest = load_json(root, "audit/reproducibility-manifest.json", issues)
    if not manifest.get("executed"):
        issues.append("Manifest does not confirm a completed execution")
    for field in ("completed_at", "command"):
        if has_placeholder(manifest.get(field)):
            issues.append(f"Reproducibility manifest is incomplete: {field}")
    environment = manifest.get("environment") or {}
    for field in ("os", "language"):
        if has_placeholder(environment.get(field)):
            issues.append(f"Environment is incomplete: {field}")
    for field in ("source_files", "output_files"):
        paths = manifest.get(field)
        if not isinstance(paths, list) or not paths:
            issues.append(f"Manifest has no {field}")
            continue
        for path in paths:
            if not relative_file_exists(root, path):
                issues.append(f"Manifest artifact is missing or outside project: {path}")
    if manifest.get("run_mode") == "demo" and not manifest.get("illustrative_only"):
        issues.append("Demo manifest must set illustrative_only to true")
    return issues


def audit_evidence(root: Path) -> list[str]:
    issues: list[str] = []
    frozen = load_json(root, "results/frozen-results.json", issues)
    if not frozen.get("frozen"):
        issues.append("Canonical results have not been frozen")
    for field in ("version", "approved_by", "approved_at"):
        if has_placeholder(frozen.get(field)):
            issues.append(f"Frozen result record is incomplete: {field}")
    metrics = frozen.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        issues.append("Frozen result record has no metrics or baseline comparison")
    else:
        for index, metric in enumerate(metrics, 1):
            for field in ("name", "baseline", "proposed", "artifact_path"):
                if has_placeholder(metric.get(field)):
                    issues.append(f"Metric {index} is incomplete: {field}")
            if not relative_file_exists(root, metric.get("artifact_path")):
                issues.append(f"Metric {index} evidence file is missing")
    validation = frozen.get("validation_evidence")
    if not isinstance(validation, list) or not validation:
        issues.append("No robustness, uncertainty, or validation evidence is recorded")
    else:
        for item in validation:
            if not relative_file_exists(root, item.get("artifact_path")):
                issues.append("A validation evidence file is missing")

    ledger_path = root / "audit/claim-evidence-ledger.csv"
    if not ledger_path.is_file():
        return issues + ["Missing audit/claim-evidence-ledger.csv"]
    try:
        with ledger_path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        return issues + [f"Cannot read claim ledger: {exc}"]
    if not rows:
        issues.append("Claim-evidence ledger has no claims")
    for row in rows:
        claim_id = row.get("claim_id") or "unknown"
        if has_placeholder(row.get("claim_text")):
            issues.append(f"Claim {claim_id} has no text")
        if row.get("validation_status") != "passed":
            issues.append(f"Claim {claim_id} has not passed validation")
        if row.get("status") != "verified":
            issues.append(f"Claim {claim_id} is not verified")
        if not relative_file_exists(root, row.get("artifact_path")):
            issues.append(f"Claim {claim_id} evidence file is missing")
    return issues


def audit_manuscript(root: Path) -> list[str]:
    issues: list[str] = []
    manuscript = root / "paper/main.md"
    if not manuscript.is_file():
        return ["Missing paper/main.md"]
    try:
        text = manuscript.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Cannot read paper/main.md: {exc}"]
    if len(text.strip()) < 300:
        issues.append("Manuscript is too short to audit")
    if "TODO" in text.upper():
        issues.append("Manuscript still contains TODO markers")
    frozen = load_json(root, "results/frozen-results.json", issues)
    version = frozen.get("version")
    if not has_placeholder(version) and f"frozen-results: {version}" not in text:
        issues.append(
            "Manuscript does not declare its canonical result version "
            f"with 'frozen-results: {version}'"
        )
    return issues


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_audit(root: Path, write_report: bool = True) -> dict[str, Any]:
    root = root.expanduser().resolve()
    audits: list[tuple[str, str, Callable[[Path], list[str]]]] = [
        ("intake", "Problem and data", audit_intake),
        ("method", "Method decision", audit_method),
        ("computation", "Executable computation", audit_computation),
        ("evidence", "Validated evidence", audit_evidence),
        ("manuscript", "Manuscript consistency", audit_manuscript),
    ]
    results: list[GateResult] = []
    upstream_passed = True
    for gate, title, function in audits:
        issues = function(root)
        if not upstream_passed:
            status = "blocked"
        elif issues:
            status = "failed"
            upstream_passed = False
        else:
            status = "passed"
        results.append(GateResult(gate, title, status, issues))

    report = {
        "schema_version": "2.0",
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "overall_status": "passed" if all(r.status == "passed" for r in results) else "failed",
        "gates": [asdict(result) for result in results],
    }
    if write_report:
        audit_dir = root / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        report_path = audit_dir / "latest-audit.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        lines = [
            "# Modeling Project Audit",
            "",
            f"- Overall: {report['overall_status']}",
            f"- Audited at: {report['audited_at']}",
            "",
        ]
        for result in results:
            lines.append(f"## {result.gate}: {result.status}")
            lines.append("")
            if result.issues:
                lines.extend(f"- {issue}" for issue in result.issues)
            else:
                lines.append("- No issues detected.")
            lines.append("")
        (audit_dir / "latest-audit.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )
        report["report_sha256"] = sha256(report_path)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit an evidence-gated mathematical-modeling project."
    )
    parser.add_argument("project_dir", type=Path)
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Print the audit without writing report files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_audit(args.project_dir, write_report=not args.no_write)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["overall_status"] == "passed" else 1)


if __name__ == "__main__":
    main()
