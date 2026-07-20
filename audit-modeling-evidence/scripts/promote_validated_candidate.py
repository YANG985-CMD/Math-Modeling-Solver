#!/usr/bin/env python3
"""Promote a modeling result only when the required validation evidence exists."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audit_candidate_evidence import audit_report


TRANSITIONS = {
    "candidate": "independently_validated",
    "independently_validated": "frozen",
    "frozen": "manuscript",
}
PROJECT_RESULT_STATUS = {
    "independently_validated": "validated",
    "frozen": "frozen",
    "manuscript": "manuscript",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_experiment(registry: dict[str, Any], experiment_id: str) -> dict[str, Any]:
    matches = [item for item in registry.get("experiments", []) if item.get("id") == experiment_id]
    if len(matches) != 1:
        raise ValueError(f"expected one experiment with id {experiment_id!r}")
    return matches[0]


def promote(
    registry_path: Path,
    experiment_id: str,
    target: str,
    evidence: Path,
    approved_by: str | None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text(encoding="utf-8-sig"))
    experiment = find_experiment(registry, experiment_id)
    current = experiment.get("status")
    expected = TRANSITIONS.get(current)
    if expected != target:
        raise ValueError(f"invalid transition {current!r} -> {target!r}; expected {expected!r}")
    evidence = evidence.expanduser().resolve()
    if not evidence.is_file() or evidence.stat().st_size == 0:
        raise ValueError(f"validation evidence is missing or empty: {evidence}")
    resolved_root = (
        project_root.expanduser().resolve()
        if project_root is not None
        else registry_path.resolve().parent.parent
        if registry_path.resolve().parent.name == "planning"
        else registry_path.resolve().parent
    )
    if target in {"independently_validated", "frozen"}:
        if evidence.suffix.lower() != ".json":
            raise ValueError(f"promotion to {target} requires a JSON validation report")
        try:
            evidence_report = json.loads(evidence.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"validation evidence is not valid JSON: {evidence}") from exc
        if not isinstance(evidence_report, dict):
            raise ValueError("validation evidence must be a JSON object")
        evidence_status = evidence_report.get(
            "status", evidence_report.get("overall_status")
        )
        if evidence_status not in {"passed", "validated", "independently_validated"}:
            raise ValueError(
                "validation evidence must declare status or overall_status as passed"
            )
        structural_issues = audit_report(
            evidence_report, resolved_root, experiment
        )
        if structural_issues:
            raise ValueError(
                "candidate validation contract failed: " + "; ".join(structural_issues)
            )
    if target == "frozen" and not approved_by:
        raise ValueError("promotion to frozen requires --approved-by")
    if target == "manuscript" and evidence.suffix.lower() not in {".md", ".tex", ".pdf"}:
        raise ValueError("manuscript promotion requires a Markdown, TeX, or PDF artifact")

    experiment["status"] = target
    experiment.setdefault("decision_log", []).append(
        {
            "at": now(),
            "from": current,
            "to": target,
            "reason": "required promotion evidence verified",
            "evidence": str(evidence),
            "approved_by": approved_by,
        }
    )
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    state_path = resolved_root / "audit" / "project-state.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        if isinstance(state, dict):
            state["result_status"] = PROJECT_RESULT_STATUS[target]
            state_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--id", required=True)
    parser.add_argument(
        "--to", dest="target", choices=tuple(TRANSITIONS.values()), required=True
    )
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--approved-by")
    parser.add_argument("--root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        experiment = promote(
            args.registry,
            args.id,
            args.target,
            args.evidence,
            args.approved_by,
            args.root,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Candidate promotion failed: {exc}")
        return 2
    print(json.dumps(experiment, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
