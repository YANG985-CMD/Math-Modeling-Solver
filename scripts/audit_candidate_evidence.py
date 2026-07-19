#!/usr/bin/env python3
"""Audit structured evidence before a modeling candidate is promoted."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


PASS_STATUSES = {"passed", "validated", "independently_validated"}
INDEPENDENCE_LEVELS = {
    "same_run_replay": 0,
    "independent_rerun": 1,
    "held_out_cases": 2,
    "external_blind_cases": 3,
}


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def sha256_text(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdefABCDEF" for character in value)
    )


def artifact_exists(root: Path, value: Any) -> bool:
    if not nonempty_text(value):
        return False
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.expanduser().resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return False
    return candidate.is_file() and candidate.stat().st_size > 0


def require_artifact(
    root: Path, block: dict[str, Any], label: str, issues: list[str]
) -> None:
    if not artifact_exists(root, block.get("artifact_path")):
        issues.append(f"{label} artifact_path is missing, empty, or outside the project")


def passed_block(
    report: dict[str, Any], name: str, root: Path, issues: list[str]
) -> dict[str, Any]:
    block = report.get(name)
    if not isinstance(block, dict):
        issues.append(f"{name} must be an object")
        return {}
    if block.get("status") not in PASS_STATUSES:
        issues.append(f"{name}.status must be passed")
    require_artifact(root, block, name, issues)
    return block


def audit_check_list(
    checks: Any,
    label: str,
    root: Path,
    issues: list[str],
    minimum: int = 1,
) -> None:
    if not isinstance(checks, list) or len(checks) < minimum:
        issues.append(f"{label} must contain at least {minimum} check(s)")
        return
    for index, check in enumerate(checks, 1):
        if not isinstance(check, dict):
            issues.append(f"{label}[{index}] must be an object")
            continue
        if not nonempty_text(check.get("name")):
            issues.append(f"{label}[{index}].name is missing")
        if check.get("status") not in PASS_STATUSES:
            issues.append(f"{label}[{index}].status must be passed")
        if not artifact_exists(root, check.get("artifact_path")):
            issues.append(f"{label}[{index}] evidence artifact is missing")


def objective_span_is_nonzero(value: Any) -> bool:
    if isinstance(value, dict):
        low, high = value.get("minimum"), value.get("maximum")
    elif isinstance(value, list) and len(value) == 2:
        low, high = value
    else:
        return False
    return finite_number(low) and finite_number(high) and float(high) > float(low)


def audit_report(
    report: dict[str, Any],
    root: Path,
    experiment: dict[str, Any] | None = None,
) -> list[str]:
    issues: list[str] = []
    if report.get("schema_version") != "1.1":
        issues.append("schema_version must be 1.1")
    if report.get("status") not in PASS_STATUSES:
        issues.append("status must declare passed, validated, or independently_validated")

    metric = report.get("primary_metric")
    if not isinstance(metric, dict):
        issues.append("primary_metric must be an object")
    else:
        if not nonempty_text(metric.get("name")):
            issues.append("primary_metric.name is missing")
        if metric.get("direction") not in {"min", "max"}:
            issues.append("primary_metric.direction must be min or max")
        for field in ("baseline", "proposed", "minimum_improvement"):
            if not finite_number(metric.get(field)):
                issues.append(f"primary_metric.{field} must be finite")
        require_artifact(root, metric, "primary_metric", issues)
        if all(
            finite_number(metric.get(field))
            for field in ("baseline", "proposed", "minimum_improvement")
        ) and metric.get("direction") in {"min", "max"}:
            baseline = float(metric["baseline"])
            proposed = float(metric["proposed"])
            improvement = (
                proposed - baseline
                if metric["direction"] == "max"
                else baseline - proposed
            )
            if improvement < float(metric["minimum_improvement"]):
                issues.append("primary metric does not meet its minimum improvement")

    feasibility = passed_block(report, "feasibility", root, issues)
    checks = feasibility.get("checks")
    if not isinstance(checks, list) or not checks:
        issues.append("feasibility.checks must not be empty")

    fidelity = report.get("fidelity")
    if not isinstance(fidelity, dict):
        issues.append("fidelity must be an object")
    elif fidelity.get("status") not in PASS_STATUSES | {"not_required"}:
        issues.append("fidelity.status must be passed or not_required")
    elif fidelity.get("status") in PASS_STATUSES:
        require_artifact(root, fidelity, "fidelity", issues)

    semantic = passed_block(report, "semantic_contract", root, issues)
    if not isinstance(semantic.get("definitions"), list) or not semantic.get("definitions"):
        issues.append("semantic_contract.definitions must not be empty")

    support = passed_block(report, "support_and_identifiability", root, issues)
    if not nonempty_text(support.get("summary")):
        issues.append("support_and_identifiability.summary is missing")
    if not isinstance(support.get("limitations"), list):
        issues.append("support_and_identifiability.limitations must be a list")

    structural = report.get("structural_validity")
    if not isinstance(structural, dict):
        issues.append("structural_validity must be an object")
    else:
        if structural.get("status") not in PASS_STATUSES:
            issues.append("structural_validity.status must be passed")
        audit_check_list(
            structural.get("checks"),
            "structural_validity.checks",
            root,
            issues,
        )

    reproducibility = passed_block(report, "reproducibility", root, issues)
    if not isinstance(reproducibility.get("independent_reruns"), int) or reproducibility.get(
        "independent_reruns", 0
    ) < 1:
        issues.append("reproducibility.independent_reruns must be at least 1")
    hashes = reproducibility.get("canonical_input_hashes")
    if not isinstance(hashes, list) or not hashes or not all(
        sha256_text(item) for item in hashes
    ):
        issues.append(
            "reproducibility.canonical_input_hashes must contain SHA-256 values"
        )

    sensitivity = report.get("sensitivity")
    if not isinstance(sensitivity, dict):
        issues.append("sensitivity must be an object")
    elif sensitivity.get("status") in PASS_STATUSES:
        parameters = sensitivity.get("parameters_tested")
        if not isinstance(parameters, list) or not any(
            nonempty_text(item) for item in parameters
        ):
            issues.append("sensitivity.parameters_tested must not be empty")
        if not nonempty_text(sensitivity.get("summary")):
            issues.append("sensitivity.summary is missing")
        require_artifact(root, sensitivity, "sensitivity", issues)
    elif sensitivity.get("status") == "not_applicable":
        if not nonempty_text(sensitivity.get("not_applicable_reason")):
            issues.append("sensitivity.not_applicable_reason is missing")
    else:
        issues.append("sensitivity.status must be passed or not_applicable")

    robustness = passed_block(report, "robustness", root, issues)
    if not isinstance(robustness.get("tested_cases"), int) or robustness.get(
        "tested_cases", 0
    ) < 1:
        issues.append("robustness.tested_cases must be at least 1")
    perturbations = robustness.get("perturbation_families")
    if not isinstance(perturbations, list) or not any(
        nonempty_text(item) for item in perturbations
    ):
        issues.append("robustness.perturbation_families must not be empty")

    generalization = report.get("generalization")
    generalization_claim = None
    if not isinstance(generalization, dict):
        issues.append("generalization must be an object")
    else:
        generalization_claim = generalization.get("claim_type")
        if generalization_claim not in {
            "instance_only",
            "tested_family",
            "external_generalization",
        }:
            issues.append("generalization.claim_type is invalid")
        limitations = generalization.get("limitations")
        if not isinstance(limitations, list):
            issues.append("generalization.limitations must be a list")
        if generalization_claim == "instance_only":
            if generalization.get("status") != "not_claimed":
                issues.append(
                    "instance_only generalization.status must be not_claimed"
                )
            if not isinstance(limitations, list) or not any(
                nonempty_text(item) for item in limitations
            ):
                issues.append(
                    "instance_only generalization must state at least one limitation"
                )
        elif generalization_claim in {"tested_family", "external_generalization"}:
            if generalization.get("status") not in PASS_STATUSES:
                issues.append("a generalization claim requires passed status")
            minimum_cases = 2 if generalization_claim == "tested_family" else 1
            if not isinstance(generalization.get("independent_cases"), int) or generalization.get(
                "independent_cases", 0
            ) < minimum_cases:
                issues.append(
                    f"{generalization_claim} requires at least {minimum_cases} independent case(s)"
                )
            if not isinstance(generalization.get("selection_free_cases"), int) or generalization.get(
                "selection_free_cases", 0
            ) < 1:
                issues.append("a generalization claim requires a selection-free case")
            require_artifact(root, generalization, "generalization", issues)

    schedule = report.get("instance_specific_schedule")
    if not isinstance(schedule, dict) or not isinstance(schedule.get("applicable"), bool):
        issues.append("instance_specific_schedule.applicable must be boolean")
    else:
        if not isinstance(schedule.get("declared"), bool):
            issues.append("instance_specific_schedule.declared must be boolean")
        if not isinstance(schedule.get("transferable_policy_claimed"), bool):
            issues.append(
                "instance_specific_schedule.transferable_policy_claimed must be boolean"
            )
        if schedule["applicable"]:
            if schedule.get("declared") is not True:
                issues.append("an instance-specific schedule must be explicitly declared")
            require_artifact(root, schedule, "instance_specific_schedule", issues)
        if schedule.get("transferable_policy_claimed"):
            if not schedule["applicable"]:
                issues.append(
                    "a transferable schedule-policy claim requires schedule applicability"
                )
            if generalization_claim == "instance_only":
                issues.append(
                    "a transferable schedule-policy claim requires generalization evidence"
                )

    independence = report.get("validation_independence_level")
    if independence not in INDEPENDENCE_LEVELS:
        issues.append("validation_independence_level is invalid")
    elif INDEPENDENCE_LEVELS[independence] < INDEPENDENCE_LEVELS["independent_rerun"]:
        issues.append(
            "independent validation requires at least an independent_rerun"
        )

    multiobjective = report.get("multiobjective")
    if not isinstance(multiobjective, dict) or not isinstance(
        multiobjective.get("applicable"), bool
    ):
        issues.append("multiobjective.applicable must be boolean")
    elif multiobjective["applicable"]:
        claim_type = multiobjective.get("claim_type")
        if claim_type not in {"single_tradeoff_candidate", "pareto_front"}:
            issues.append("multiobjective.claim_type is invalid")
        points = multiobjective.get("nondominated_points")
        if not isinstance(points, int) or points < 1:
            issues.append("multiobjective.nondominated_points must be at least 1")
        require_artifact(root, multiobjective, "multiobjective", issues)
        if claim_type == "pareto_front":
            if not isinstance(points, int) or points < 2:
                issues.append("a Pareto-front claim requires at least two points")
            spans = multiobjective.get("objective_spans")
            if not isinstance(spans, list) or len(spans) < 2:
                issues.append("a Pareto-front claim requires at least two objective spans")
            elif not all(objective_span_is_nonzero(item) for item in spans):
                issues.append("every Pareto objective span must be non-zero")

    pipeline = report.get("pipeline")
    if not isinstance(pipeline, dict) or not isinstance(pipeline.get("applicable"), bool):
        issues.append("pipeline.applicable must be boolean")
    elif pipeline["applicable"]:
        audit_check_list(
            pipeline.get("stage_checks"),
            "pipeline.stage_checks",
            root,
            issues,
            minimum=2,
        )
        if not nonempty_text(pipeline.get("uncertainty_propagation")):
            issues.append("pipeline.uncertainty_propagation is missing")
        require_artifact(root, pipeline, "pipeline", issues)

    if not isinstance(report.get("known_failure_regions"), list):
        issues.append("known_failure_regions must be a list")
    boundary = report.get("claim_boundary")
    if not isinstance(boundary, list) or not any(nonempty_text(item) for item in boundary):
        issues.append("claim_boundary must contain at least one statement")

    if experiment is not None and isinstance(metric, dict):
        expected_name = experiment.get("primary_metric")
        expected_direction = experiment.get("direction")
        if metric.get("name") != expected_name:
            issues.append("primary metric name does not match the experiment registry")
        if metric.get("direction") != expected_direction:
            issues.append("primary metric direction does not match the experiment registry")
        for report_field, experiment_field in (
            ("baseline", "baseline"),
            ("minimum_improvement", "minimum_improvement"),
        ):
            left, right = metric.get(report_field), experiment.get(experiment_field)
            if finite_number(left) and finite_number(right) and not math.isclose(
                float(left), float(right), rel_tol=1e-9, abs_tol=1e-12
            ):
                issues.append(
                    f"primary_metric.{report_field} does not match the experiment registry"
                )
    return issues


def load_experiment(path: Path, experiment_id: str) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8-sig"))
    matches = [
        item
        for item in registry.get("experiments", [])
        if item.get("id") == experiment_id
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one experiment with id {experiment_id!r}")
    return matches[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--experiment-registry", type=Path)
    parser.add_argument("--id")
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report_path = args.report.expanduser().resolve()
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
        if not isinstance(report, dict):
            raise ValueError("candidate validation report must be a JSON object")
        root = (args.root or report_path.parent).expanduser().resolve()
        experiment = None
        if args.experiment_registry or args.id:
            if not args.experiment_registry or not args.id:
                raise ValueError("--experiment-registry and --id must be used together")
            experiment = load_experiment(args.experiment_registry, args.id)
        issues = audit_report(report, root, experiment)
        output = {
            "schema_version": "1.1",
            "status": "passed" if not issues else "failed",
            "report": str(report_path),
            "root": str(root),
            "issue_count": len(issues),
            "issues": issues,
        }
        rendered = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if not issues else 1
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "issues": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
