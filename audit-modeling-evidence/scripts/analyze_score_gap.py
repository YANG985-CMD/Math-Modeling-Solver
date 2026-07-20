#!/usr/bin/env python3
"""Diagnose weighted score gaps before starting an optimization campaign."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"


class InputError(ValueError):
    """Raised when the score contract is incomplete or internally inconsistent."""


def finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise InputError(f"{field} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"{field} must be a finite number") from exc
    if not math.isfinite(result):
        raise InputError(f"{field} must be a finite number")
    return result


def utility(value: float, worst: float, best: float, direction: str) -> float:
    if direction == "max":
        return (value - worst) / (best - worst)
    return (worst - value) / (worst - best)


def validate_value(name: str, field: str, value: float, worst: float, best: float) -> None:
    lower, upper = sorted((worst, best))
    tolerance = max(1.0, abs(lower), abs(upper)) * 1e-12
    if value < lower - tolerance or value > upper + tolerance:
        raise InputError(
            f"component {name!r}: {field}={value} is outside the declared "
            f"range [{lower}, {upper}]"
        )


def diagnose(payload: dict[str, Any]) -> dict[str, Any]:
    components = payload.get("components")
    if not isinstance(components, list) or not components:
        raise InputError("components must be a non-empty list")

    rows: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    for index, raw in enumerate(components, start=1):
        if not isinstance(raw, dict):
            raise InputError(f"components[{index}] must be an object")
        name = str(raw.get("name", "")).strip()
        if not name or name in seen_names:
            raise InputError(f"components[{index}].name must be non-empty and unique")
        seen_names.add(name)
        direction = str(raw.get("direction", "")).lower()
        if direction not in {"max", "min"}:
            raise InputError(f"component {name!r}: direction must be 'max' or 'min'")
        weight = finite_number(raw.get("weight"), f"component {name!r}.weight")
        if weight <= 0:
            raise InputError(f"component {name!r}: weight must be positive")
        worst = finite_number(raw.get("worst"), f"component {name!r}.worst")
        best = finite_number(
            raw.get("theoretical_best"), f"component {name!r}.theoretical_best"
        )
        baseline = finite_number(raw.get("baseline"), f"component {name!r}.baseline")
        if best == worst:
            raise InputError(f"component {name!r}: best and worst must differ")
        if direction == "max" and best < worst:
            raise InputError(f"component {name!r}: max objective requires best > worst")
        if direction == "min" and best > worst:
            raise InputError(f"component {name!r}: min objective requires best < worst")
        validate_value(name, "baseline", baseline, worst, best)

        reference_raw = raw.get("reference")
        reference = None
        if reference_raw is not None:
            reference = finite_number(reference_raw, f"component {name!r}.reference")
            validate_value(name, "reference", reference, worst, best)

        baseline_utility = utility(baseline, worst, best, direction)
        reference_utility = (
            utility(reference, worst, best, direction) if reference is not None else None
        )
        weighted_baseline = weight * baseline_utility
        weighted_headroom = weight * max(0.0, 1.0 - baseline_utility)
        weighted_reference_gap = (
            weight * max(0.0, reference_utility - baseline_utility)
            if reference_utility is not None
            else None
        )
        raw_range = abs(best - worst)
        rows.append(
            {
                "name": name,
                "direction": direction,
                "weight": weight,
                "worst": worst,
                "theoretical_best": best,
                "baseline": baseline,
                "reference": reference,
                "baseline_utility": baseline_utility,
                "reference_utility": reference_utility,
                "weighted_baseline_score": weighted_baseline,
                "weighted_headroom_to_bound": weighted_headroom,
                "weighted_gap_to_reference": weighted_reference_gap,
                "marginal_weighted_gain_per_raw_unit": weight / raw_range,
            }
        )

    weight_sum = sum(row["weight"] for row in rows)
    baseline_score = sum(row["weighted_baseline_score"] for row in rows)
    references_complete = all(row["reference_utility"] is not None for row in rows)
    reference_score = (
        sum(row["weight"] * row["reference_utility"] for row in rows)
        if references_complete
        else None
    )

    headroom_order = sorted(
        rows, key=lambda row: (-row["weighted_headroom_to_bound"], row["name"])
    )
    for rank, row in enumerate(headroom_order, start=1):
        row["headroom_priority_rank"] = rank
    reference_order = sorted(
        (row for row in rows if row["weighted_gap_to_reference"] is not None),
        key=lambda row: (-row["weighted_gap_to_reference"], row["name"]),
    )
    for rank, row in enumerate(reference_order, start=1):
        row["reference_priority_rank"] = rank
    for row in rows:
        row.setdefault("reference_priority_rank", None)

    positive_reference_gaps = [
        row for row in reference_order if row["weighted_gap_to_reference"] > 0
    ]
    focus_basis = "gap_to_reference" if positive_reference_gaps else "headroom_to_bound"
    focus_rows = positive_reference_gaps or headroom_order

    return {
        "schema_version": SCHEMA_VERSION,
        "objective": payload.get("objective", "weighted normalized score"),
        "scoring_assumption": (
            "Additive weighted utilities normalized between each declared worst "
            "value and theoretical best value."
        ),
        "summary": {
            "weight_sum": weight_sum,
            "baseline_weighted_score": baseline_score,
            "baseline_score_ratio": baseline_score / weight_sum,
            "theoretical_weighted_upper_bound": weight_sum,
            "weighted_headroom_to_bound": weight_sum - baseline_score,
            "reference_weighted_score": reference_score,
            "weighted_gap_to_reference": (
                max(0.0, reference_score - baseline_score)
                if reference_score is not None
                else None
            ),
            "reference_is_complete": references_complete,
        },
        "recommended_focus_basis": focus_basis,
        "recommended_focus": [row["name"] for row in focus_rows],
        "components": rows,
    }


def write_outputs(report: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "score-gap-analysis.json"
    csv_path = out_dir / "score-gap-components.csv"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    fields = list(report["components"][0].keys())
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["components"])
    return json_path, csv_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON score contract")
    parser.add_argument("--out-dir", type=Path, default=Path("score-gap-analysis"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise InputError("input JSON must be an object")
        report = diagnose(payload)
        json_path, csv_path = write_outputs(report, args.out_dir)
    except (OSError, json.JSONDecodeError, InputError) as exc:
        print(f"Score-gap analysis failed: {exc}")
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
