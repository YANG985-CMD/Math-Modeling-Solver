#!/usr/bin/env python3
"""Register bounded optimization experiments and record promotion decisions."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.1"
ACTIVE_STATUSES = {"exploratory", "candidate"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "experiments": []}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or not isinstance(value.get("experiments"), list):
        raise ValueError("registry must be an object containing an experiments list")
    value["schema_version"] = SCHEMA_VERSION
    return value


def write_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def find_experiment(registry: dict[str, Any], experiment_id: str) -> dict[str, Any]:
    matches = [item for item in registry["experiments"] if item.get("id") == experiment_id]
    if len(matches) != 1:
        raise ValueError(f"expected one experiment with id {experiment_id!r}")
    return matches[0]


def improvement(value: float, baseline: float, direction: str) -> float:
    return value - baseline if direction == "max" else baseline - value


def project_root_for_registry(path: Path) -> Path:
    parent = path.expanduser().resolve().parent
    return parent.parent if parent.name == "planning" else parent


def require_artifact(path: Path, value: str) -> None:
    root = project_root_for_registry(path)
    artifact = Path(value)
    if not artifact.is_absolute():
        artifact = root / artifact
    artifact = artifact.expanduser().resolve()
    try:
        artifact.relative_to(root)
    except ValueError as exc:
        raise ValueError("run artifact must stay inside the project root") from exc
    if not artifact.is_file() or artifact.stat().st_size == 0:
        raise ValueError(f"run artifact is missing or empty: {artifact}")


def family_members(
    registry: dict[str, Any], family: str
) -> list[dict[str, Any]]:
    return [
        item
        for item in registry["experiments"]
        if item.get("experiment_family") == family
    ]


def planned_candidates(experiment: dict[str, Any]) -> int:
    budget = experiment.get("budget", {})
    value = budget.get("candidate_evaluations", budget.get("maximum_runs", 0))
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def consumed_candidates(experiment: dict[str, Any]) -> int:
    return sum(
        item.get("candidates_evaluated", 0)
        for item in experiment.get("runs", [])
        if isinstance(item.get("candidates_evaluated", 0), int)
        and not isinstance(item.get("candidates_evaluated", 0), bool)
    )


def register(args: argparse.Namespace, registry: dict[str, Any]) -> None:
    if any(item.get("id") == args.id for item in registry["experiments"]):
        raise ValueError(f"experiment id already exists: {args.id}")
    members = family_members(registry, args.experiment_family)
    if args.parent_experiment:
        parent = find_experiment(registry, args.parent_experiment)
        if parent.get("experiment_family") != args.experiment_family:
            raise ValueError("parent experiment must belong to the same experiment family")
    family_caps = {
        item.get("cumulative_candidate_budget")
        for item in members
        if isinstance(item.get("cumulative_candidate_budget"), int)
    }
    if family_caps and family_caps != {args.cumulative_candidate_budget}:
        raise ValueError("all experiments in a family must use one cumulative budget")
    planned_before = sum(planned_candidates(item) for item in members)
    planned_after = planned_before + args.candidate_budget
    if planned_after > args.cumulative_candidate_budget:
        raise ValueError(
            "experiment family candidate budget would be exceeded: "
            f"{planned_after} > {args.cumulative_candidate_budget}"
        )
    registry["experiments"].append(
        {
            "id": args.id,
            "created_at": now(),
            "parent_experiment": args.parent_experiment,
            "experiment_family": args.experiment_family,
            "cumulative_candidate_budget": args.cumulative_candidate_budget,
            "adaptive_search_bias_notes": args.adaptive_search_bias_notes,
            "hypothesis": args.hypothesis,
            "primary_metric": args.metric,
            "direction": args.direction,
            "baseline": args.baseline,
            "minimum_improvement": args.min_improvement,
            "budget": {
                "maximum_runs": args.max_runs,
                "maximum_runtime_minutes": args.max_runtime_minutes,
                "candidate_evaluations": args.candidate_budget,
                "family_planned_before": planned_before,
                "family_planned_after": planned_after,
            },
            "promotion_rule": (
                "feasible and fidelity-passed result with improvement at or above "
                "minimum_improvement becomes candidate"
            ),
            "stop_condition": args.stop_condition,
            "status": "exploratory",
            "runs": [],
            "best_run": None,
            "decision_log": [],
        }
    )


def record(
    args: argparse.Namespace, registry: dict[str, Any], registry_path: Path
) -> None:
    experiment = find_experiment(registry, args.id)
    if experiment["status"] not in ACTIVE_STATUSES:
        raise ValueError(f"cannot record a run for terminal status {experiment['status']!r}")
    if len(experiment["runs"]) >= experiment["budget"]["maximum_runs"]:
        raise ValueError("maximum run budget is already exhausted")
    value = float(args.value)
    if not math.isfinite(value):
        raise ValueError("value must be finite")
    if args.candidates_evaluated < 1:
        raise ValueError("candidates evaluated must be positive")
    if not math.isfinite(args.runtime_minutes) or args.runtime_minutes <= 0:
        raise ValueError("runtime minutes must be finite and positive")
    require_artifact(registry_path, args.artifact)
    experiment_candidates = consumed_candidates(experiment) + args.candidates_evaluated
    if experiment_candidates > planned_candidates(experiment):
        raise ValueError("experiment candidate-evaluation budget would be exceeded")
    runtime_used = sum(
        float(item.get("runtime_minutes", 0)) for item in experiment["runs"]
    ) + args.runtime_minutes
    if runtime_used > float(experiment["budget"]["maximum_runtime_minutes"]):
        raise ValueError("experiment runtime budget would be exceeded")
    members = family_members(registry, experiment["experiment_family"])
    family_consumed = sum(consumed_candidates(item) for item in members)
    if family_consumed + args.candidates_evaluated > experiment["cumulative_candidate_budget"]:
        raise ValueError("experiment family cumulative candidate budget would be exceeded")
    run = {
        "run_id": args.run_id or f"run-{len(experiment['runs']) + 1}",
        "recorded_at": now(),
        "value": value,
        "improvement": improvement(value, experiment["baseline"], experiment["direction"]),
        "feasible": args.feasible,
        "fidelity": args.fidelity,
        "candidates_evaluated": args.candidates_evaluated,
        "runtime_minutes": args.runtime_minutes,
        "artifact": args.artifact,
        "notes": args.notes,
    }
    experiment["runs"].append(run)
    eligible = [
        item
        for item in experiment["runs"]
        if item["feasible"] and item["fidelity"] in {"passed", "not_required"}
    ]
    if eligible:
        experiment["best_run"] = max(eligible, key=lambda item: item["improvement"])["run_id"]
    threshold_met = any(
        item["improvement"] >= experiment["minimum_improvement"] for item in eligible
    )

    previous = experiment["status"]
    if not run["feasible"]:
        experiment["status"] = "rejected_infeasible"
    elif run["fidelity"] == "failed":
        experiment["status"] = "rejected_fidelity_failure"
    elif threshold_met:
        experiment["status"] = "candidate"
    elif len(experiment["runs"]) >= experiment["budget"]["maximum_runs"]:
        experiment["status"] = "rejected_no_improvement"
    else:
        experiment["status"] = "exploratory"
    experiment["decision_log"].append(
        {
            "at": now(),
            "from": previous,
            "to": experiment["status"],
            "reason": (
                "hard feasibility failure"
                if not run["feasible"]
                else "transition fidelity failure"
                if run["fidelity"] == "failed"
                else "promotion threshold met"
                if experiment["status"] == "candidate"
                else "run budget exhausted without threshold improvement"
                if experiment["status"] == "rejected_no_improvement"
                else "continue within registered budget"
            ),
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--id", required=True)
    create.add_argument("--experiment-family", required=True)
    create.add_argument("--parent-experiment")
    create.add_argument("--candidate-budget", type=int, required=True)
    create.add_argument("--cumulative-candidate-budget", type=int, required=True)
    create.add_argument("--adaptive-search-bias-notes", required=True)
    create.add_argument("--hypothesis", required=True)
    create.add_argument("--metric", required=True)
    create.add_argument("--direction", choices=("max", "min"), required=True)
    create.add_argument("--baseline", type=float, required=True)
    create.add_argument("--min-improvement", type=float, required=True)
    create.add_argument("--max-runs", type=int, required=True)
    create.add_argument("--max-runtime-minutes", type=float, required=True)
    create.add_argument("--stop-condition", required=True)

    add = subparsers.add_parser("record")
    add.add_argument("--id", required=True)
    add.add_argument("--run-id")
    add.add_argument("--value", type=float, required=True)
    add.add_argument("--feasible", action=argparse.BooleanOptionalAction, required=True)
    add.add_argument(
        "--fidelity", choices=("passed", "failed", "not_required"), required=True
    )
    add.add_argument("--candidates-evaluated", type=int, required=True)
    add.add_argument("--runtime-minutes", type=float, required=True)
    add.add_argument("--artifact", required=True)
    add.add_argument("--notes", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create":
            if (
                args.min_improvement <= 0
                or args.max_runs < 1
                or args.max_runtime_minutes <= 0
                or args.candidate_budget < 1
                or args.cumulative_candidate_budget < args.candidate_budget
                or not args.adaptive_search_bias_notes.strip()
            ):
                raise ValueError("improvement and budget values must be positive")
        registry = read_registry(args.registry)
        if args.command == "create":
            register(args, registry)
        else:
            record(args, registry, args.registry)
        write_registry(args.registry, registry)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Experiment registry update failed: {exc}")
        return 2
    experiment = find_experiment(registry, args.id)
    print(json.dumps(experiment, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
