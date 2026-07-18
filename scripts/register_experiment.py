#!/usr/bin/env python3
"""Register bounded optimization experiments and record promotion decisions."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
ACTIVE_STATUSES = {"exploratory", "candidate"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "experiments": []}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or not isinstance(value.get("experiments"), list):
        raise ValueError("registry must be an object containing an experiments list")
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


def register(args: argparse.Namespace, registry: dict[str, Any]) -> None:
    if any(item.get("id") == args.id for item in registry["experiments"]):
        raise ValueError(f"experiment id already exists: {args.id}")
    registry["experiments"].append(
        {
            "id": args.id,
            "created_at": now(),
            "hypothesis": args.hypothesis,
            "primary_metric": args.metric,
            "direction": args.direction,
            "baseline": args.baseline,
            "minimum_improvement": args.min_improvement,
            "budget": {
                "maximum_runs": args.max_runs,
                "maximum_runtime_minutes": args.max_runtime_minutes,
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


def record(args: argparse.Namespace, registry: dict[str, Any]) -> None:
    experiment = find_experiment(registry, args.id)
    if experiment["status"] not in ACTIVE_STATUSES:
        raise ValueError(f"cannot record a run for terminal status {experiment['status']!r}")
    value = float(args.value)
    if not math.isfinite(value):
        raise ValueError("value must be finite")
    run = {
        "run_id": args.run_id or f"run-{len(experiment['runs']) + 1}",
        "recorded_at": now(),
        "value": value,
        "improvement": improvement(value, experiment["baseline"], experiment["direction"]),
        "feasible": args.feasible,
        "fidelity": args.fidelity,
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

    previous = experiment["status"]
    if not run["feasible"]:
        experiment["status"] = "rejected_infeasible"
    elif run["fidelity"] == "failed":
        experiment["status"] = "rejected_fidelity_failure"
    elif run["improvement"] >= experiment["minimum_improvement"]:
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
    add.add_argument("--artifact", required=True)
    add.add_argument("--notes", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create":
            if args.min_improvement <= 0 or args.max_runs < 1 or args.max_runtime_minutes <= 0:
                raise ValueError("improvement and budget values must be positive")
        registry = read_registry(args.registry)
        if args.command == "create":
            register(args, registry)
        else:
            record(args, registry)
        write_registry(args.registry, registry)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Experiment registry update failed: {exc}")
        return 2
    experiment = find_experiment(registry, args.id)
    print(json.dumps(experiment, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
