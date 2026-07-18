#!/usr/bin/env python3
"""Compare a search surrogate trajectory with an exact simulator step by step."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
REQUIRED_FIELDS = ("step", "time", "state", "action", "feasible_actions")


class InputError(ValueError):
    """Raised when a trajectory violates the comparison contract."""


def load_trajectory(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(value, dict):
        value = value.get("trajectory")
    if not isinstance(value, list):
        raise InputError(f"{path}: expected a list or an object with 'trajectory'")
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            raise InputError(f"{path}: trajectory[{index}] must be an object")
        missing = [field for field in REQUIRED_FIELDS if field not in record]
        if missing:
            raise InputError(f"{path}: trajectory[{index}] missing {missing}")
        if not isinstance(record["feasible_actions"], list):
            raise InputError(
                f"{path}: trajectory[{index}].feasible_actions must be a list"
            )
    return value


def close_number(left: Any, right: Any, atol: float, rtol: float) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left == right
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return False
    if not math.isfinite(float(left)) or not math.isfinite(float(right)):
        return left == right
    return math.isclose(float(left), float(right), abs_tol=atol, rel_tol=rtol)


def differences(
    left: Any, right: Any, path: str, atol: float, rtol: float
) -> list[dict[str, Any]]:
    if isinstance(left, dict) and isinstance(right, dict):
        output: list[dict[str, Any]] = []
        for key in sorted(left.keys() | right.keys()):
            child = f"{path}.{key}"
            if key not in left or key not in right:
                output.append({"path": child, "surrogate": left.get(key), "exact": right.get(key)})
            else:
                output.extend(differences(left[key], right[key], child, atol, rtol))
        return output
    if isinstance(left, list) and isinstance(right, list):
        output = []
        if len(left) != len(right):
            output.append({"path": f"{path}.length", "surrogate": len(left), "exact": len(right)})
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            output.extend(
                differences(left_item, right_item, f"{path}[{index}]", atol, rtol)
            )
        return output
    equal = close_number(left, right, atol, rtol) if (
        isinstance(left, (int, float)) and isinstance(right, (int, float))
    ) else left == right
    return [] if equal else [{"path": path, "surrogate": left, "exact": right}]


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compare(
    surrogate: list[dict[str, Any]],
    exact: list[dict[str, Any]],
    *,
    min_steps: int = 50,
    atol: float = 1e-9,
    rtol: float = 1e-7,
    max_details: int = 100,
) -> dict[str, Any]:
    mismatch_types: Counter[str] = Counter()
    details: list[dict[str, Any]] = []

    def add(kind: str, step: Any, detail: Any) -> None:
        mismatch_types[kind] += 1
        if len(details) < max_details:
            details.append({"type": kind, "step": step, "detail": detail})

    if len(surrogate) != len(exact):
        add("trajectory_length", None, {"surrogate": len(surrogate), "exact": len(exact)})

    for index, (left, right) in enumerate(zip(surrogate, exact)):
        step = right.get("step", index)
        for field in ("step", "time", "state", "action"):
            diff = differences(left[field], right[field], field, atol, rtol)
            if diff:
                add(f"{field}_mismatch", step, diff)

        left_actions = Counter(canonical(item) for item in left["feasible_actions"])
        right_actions = Counter(canonical(item) for item in right["feasible_actions"])
        if left_actions != right_actions:
            add(
                "feasible_action_set_mismatch",
                step,
                {
                    "surrogate_only": list((left_actions - right_actions).elements()),
                    "exact_only": list((right_actions - left_actions).elements()),
                },
            )
        if canonical(left["action"]) not in right_actions:
            add(
                "selected_action_infeasible_in_exact_simulator",
                step,
                {"selected_action": left["action"]},
            )
        if canonical(right["action"]) not in right_actions:
            add(
                "exact_trace_selected_action_infeasible",
                step,
                {"selected_action": right["action"]},
            )

    checked_steps = min(len(surrogate), len(exact))
    coverage_passed = checked_steps >= min_steps
    if not coverage_passed:
        add("insufficient_comparison_steps", None, {"checked": checked_steps, "required": min_steps})
    mismatch_count = sum(mismatch_types.values())
    passed = mismatch_count == 0
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "passed" if passed else "failed",
        "contract": {
            "required_fields": list(REQUIRED_FIELDS),
            "minimum_steps": min_steps,
            "absolute_tolerance": atol,
            "relative_tolerance": rtol,
        },
        "summary": {
            "surrogate_steps": len(surrogate),
            "exact_steps": len(exact),
            "checked_steps": checked_steps,
            "coverage_passed": coverage_passed,
            "mismatch_count": mismatch_count,
            "mismatch_types": dict(sorted(mismatch_types.items())),
            "details_truncated": mismatch_count > len(details),
        },
        "mismatches": details,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("surrogate", type=Path)
    parser.add_argument("exact", type=Path)
    parser.add_argument("--min-steps", type=int, default=50)
    parser.add_argument("--atol", type=float, default=1e-9)
    parser.add_argument("--rtol", type=float, default=1e-7)
    parser.add_argument("--out", type=Path, default=Path("transition-fidelity.json"))
    args = parser.parse_args()
    if args.min_steps < 1 or args.atol < 0 or args.rtol < 0:
        parser.error("minimum steps and tolerances must be non-negative; min-steps must be positive")
    return args


def main() -> int:
    args = parse_args()
    try:
        surrogate = load_trajectory(args.surrogate)
        exact = load_trajectory(args.exact)
        report = compare(
            surrogate,
            exact,
            min_steps=args.min_steps,
            atol=args.atol,
            rtol=args.rtol,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except (OSError, json.JSONDecodeError, InputError) as exc:
        print(f"Transition-fidelity check failed: {exc}")
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Report: {args.out}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
