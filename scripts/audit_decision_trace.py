#!/usr/bin/env python3
"""Audit two path-dependent decision traces and locate their first divergence."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def finite(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def artifact_exists(root: Path, value: Any) -> bool:
    if not text(value):
        return False
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.expanduser().resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False
    return path.is_file() and path.stat().st_size > 0


def string_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(text(item) for item in value)
        and len(value) == len(set(value))
    )


def audit_run(
    run: Any, label: str, root: Path, issues: list[str]
) -> list[dict[str, Any]]:
    if not isinstance(run, dict):
        issues.append(f"{label} must be an object")
        return []
    if not text(run.get("id")):
        issues.append(f"{label}.id is missing")
    if not artifact_exists(root, run.get("artifact_path")):
        issues.append(f"{label}.artifact_path is missing, empty, or outside the project")
    if not finite(run.get("final_score")):
        issues.append(f"{label}.final_score must be finite")
    steps = run.get("steps")
    if not isinstance(steps, list) or not steps:
        issues.append(f"{label}.steps must not be empty")
        return []
    for index, step in enumerate(steps, 1):
        location = f"{label}.steps[{index}]"
        if not isinstance(step, dict):
            issues.append(f"{location} must be an object")
            continue
        if step.get("step") != index:
            issues.append(f"{location}.step must equal {index}")
        if not text(step.get("state_hash")):
            issues.append(f"{location}.state_hash is missing")
        available = step.get("available_actions")
        feasible = step.get("feasible_actions")
        if not string_list(available):
            issues.append(f"{location}.available_actions must be a unique string list")
        if not string_list(feasible):
            issues.append(f"{location}.feasible_actions must be a unique string list")
        if string_list(available) and string_list(feasible) and not set(feasible).issubset(
            available
        ):
            issues.append(f"{location}.feasible_actions must be a subset of available_actions")
        if not text(step.get("selected_action")):
            issues.append(f"{location}.selected_action is missing")
        elif string_list(feasible) and step["selected_action"] not in feasible:
            issues.append(f"{location}.selected_action is not feasible")
        if not finite(step.get("score_after")):
            issues.append(f"{location}.score_after must be finite")
    last_score = steps[-1].get("score_after") if isinstance(steps[-1], dict) else None
    if finite(last_score) and finite(run.get("final_score")) and not math.isclose(
        float(last_score), float(run["final_score"]), rel_tol=1e-9, abs_tol=1e-12
    ):
        issues.append(f"{label}.final_score does not match the last step")
    return [step for step in steps if isinstance(step, dict)]


def first_divergence(
    baseline: list[dict[str, Any]], intervention: list[dict[str, Any]], field: str
) -> int | None:
    for index, (left, right) in enumerate(zip(baseline, intervention), 1):
        left_value = left.get(field)
        right_value = right.get(field)
        if field.endswith("_actions"):
            left_value = sorted(left_value) if isinstance(left_value, list) else left_value
            right_value = sorted(right_value) if isinstance(right_value, list) else right_value
        if left_value != right_value:
            return index
    if len(baseline) != len(intervention):
        return min(len(baseline), len(intervention)) + 1
    return None


def audit(report: dict[str, Any], root: Path) -> dict[str, Any]:
    issues: list[str] = []
    if report.get("schema_version") != "1.0":
        issues.append("schema_version must be 1.0")
    direction = report.get("score_direction")
    if direction not in {"min", "max"}:
        issues.append("score_direction must be min or max")
    baseline = audit_run(report.get("baseline"), "baseline", root, issues)
    intervention = audit_run(
        report.get("intervention"), "intervention", root, issues
    )
    baseline_score = report.get("baseline", {}).get("final_score")
    intervention_score = report.get("intervention", {}).get("final_score")
    score_improvement = None
    if finite(baseline_score) and finite(intervention_score) and direction in {"min", "max"}:
        score_improvement = (
            float(intervention_score) - float(baseline_score)
            if direction == "max"
            else float(baseline_score) - float(intervention_score)
        )
    action_divergence = first_divergence(
        baseline, intervention, "selected_action"
    )
    return {
        "schema_version": "1.0",
        "status": "passed" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues,
        "baseline_steps": len(baseline),
        "intervention_steps": len(intervention),
        "first_available_set_divergence_step": first_divergence(
            baseline, intervention, "available_actions"
        ),
        "first_filter_divergence_step": first_divergence(
            baseline, intervention, "feasible_actions"
        ),
        "first_action_divergence_step": action_divergence,
        "path_dependence_observed": action_divergence is not None,
        "downstream_score_improvement": score_improvement,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        trace = args.trace.expanduser().resolve()
        report = json.loads(trace.read_text(encoding="utf-8-sig"))
        if not isinstance(report, dict):
            raise ValueError("trace must be a JSON object")
        result = audit(report, (args.root or trace.parent).expanduser().resolve())
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if result["status"] == "passed" else 1
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "issues": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
