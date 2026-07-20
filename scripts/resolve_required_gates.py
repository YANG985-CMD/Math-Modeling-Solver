#!/usr/bin/env python3
"""Resolve only the modeling evidence gates required at the current stage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


PROFILE_ORDER = {"explore": 0, "candidate": 1, "delivery": 2}
OPTIMIZATION_FAMILIES = {"optimization", "scheduling", "control", "simulation"}
TABULAR_FAMILIES = {
    "prediction",
    "classification",
    "clustering",
    "estimation",
    "evaluation",
}
PAPER_DELIVERIES = {"word-only", "paper-bundle", "cumcm-latex"}


def always(_: dict[str, Any]) -> bool:
    return True


def feature(name: str) -> Callable[[dict[str, Any]], bool]:
    return lambda context: name in context["features"]


def any_feature(*names: str) -> Callable[[dict[str, Any]], bool]:
    return lambda context: bool(set(names) & context["features"])


def not_feature(name: str) -> Callable[[dict[str, Any]], bool]:
    return lambda context: name not in context["features"]


def delivery_in(*names: str) -> Callable[[dict[str, Any]], bool]:
    return lambda context: context["delivery_profile"] in set(names)


GATES: list[dict[str, Any]] = [
    {
        "gate": "problem_contract",
        "minimum_profile": "explore",
        "applies": always,
        "reason": "Fix objectives, inputs, outputs, units, and assumptions before computation.",
    },
    {
        "gate": "semantic_contract",
        "minimum_profile": "explore",
        "applies": always,
        "reason": "Align metric formulas, signs, axes, units, and constraint meanings.",
    },
    {
        "gate": "executed_baseline",
        "minimum_profile": "explore",
        "applies": always,
        "reason": "Establish an executable reference before adding complexity.",
    },
    {
        "gate": "inspectable_run_artifact",
        "minimum_profile": "explore",
        "applies": always,
        "reason": "Keep code, command, and output evidence for every claimed run.",
    },
    {
        "gate": "dataset_audit",
        "minimum_profile": "explore",
        "applies": lambda context: context["task_family"] in TABULAR_FAMILIES
        or "tabular_data" in context["features"],
        "reason": "Tabular modeling requires missingness, leakage, unit, and split checks.",
    },
    {
        "gate": "hard_constraint_action_space",
        "minimum_profile": "explore",
        "applies": lambda context: context["task_family"] in OPTIMIZATION_FAMILIES,
        "reason": "Illegal decisions must be removed before optimization or simulation.",
    },
    {
        "gate": "candidate_comparison",
        "minimum_profile": "candidate",
        "applies": always,
        "reason": "Compare the promoted method fairly with its executed baseline.",
    },
    {
        "gate": "experiment_family_budget",
        "minimum_profile": "candidate",
        "applies": lambda context: context["task_family"] in OPTIMIZATION_FAMILIES,
        "reason": "Count adaptive search across related optimization experiments.",
    },
    {
        "gate": "exact_simulator_validation",
        "minimum_profile": "candidate",
        "applies": lambda context: context["task_family"] in OPTIMIZATION_FAMILIES,
        "reason": "Validate promoted decisions with the authoritative simulator.",
    },
    {
        "gate": "transition_fidelity",
        "minimum_profile": "candidate",
        "applies": any_feature("surrogate_dynamics", "learned_policy", "mpc_surrogate"),
        "reason": "A surrogate-backed search requires stepwise agreement with exact dynamics.",
    },
    {
        "gate": "decision_trace",
        "minimum_profile": "candidate",
        "applies": any_feature("path_dependent", "rolling_policy", "case_tuned_guard"),
        "reason": "Path-dependent claims require candidate sets, masks, actions, and first divergence.",
    },
    {
        "gate": "matlab_python_bridge",
        "minimum_profile": "candidate",
        "applies": feature("mixed_backend"),
        "reason": "Mixed MATLAB-Python computation requires a real round-trip preflight.",
    },
    {
        "gate": "sensitivity",
        "minimum_profile": "candidate",
        "applies": not_feature("parameter_free"),
        "reason": "Promoted parameters or policy choices require controlled variation.",
    },
    {
        "gate": "robustness",
        "minimum_profile": "candidate",
        "applies": always,
        "reason": "A candidate needs seed, noise, disruption, or scenario evidence.",
    },
    {
        "gate": "instance_claim_boundary",
        "minimum_profile": "candidate",
        "applies": lambda context: context["task_family"] == "scheduling"
        or "instance_specific" in context["features"]
        or "case_tuned_guard" in context["features"],
        "reason": "Declare an instance solution unless selection-free cases support transfer.",
    },
    {
        "gate": "generalization",
        "minimum_profile": "candidate",
        "applies": feature("transferable_claim"),
        "reason": "A transferable claim requires selection-free validation cases.",
    },
    {
        "gate": "multiobjective_coverage",
        "minimum_profile": "candidate",
        "applies": feature("multiobjective"),
        "reason": "A Pareto claim requires multiple non-dominated points with non-zero spans.",
    },
    {
        "gate": "pipeline_uncertainty",
        "minimum_profile": "candidate",
        "applies": feature("multi_stage"),
        "reason": "Validate each stage and propagate uncertainty into the final decision.",
    },
    {
        "gate": "candidate_evidence_contract",
        "minimum_profile": "candidate",
        "applies": always,
        "reason": "Promote only evidence-backed feasible candidates.",
    },
    {
        "gate": "frozen_results",
        "minimum_profile": "delivery",
        "applies": always,
        "reason": "Freeze canonical numbers before manuscript generation.",
    },
    {
        "gate": "claim_evidence_ledger",
        "minimum_profile": "delivery",
        "applies": delivery_in(*PAPER_DELIVERIES),
        "reason": "Every manuscript claim must link to a verified result artifact.",
    },
    {
        "gate": "figure_qa",
        "minimum_profile": "delivery",
        "applies": delivery_in(*PAPER_DELIVERIES),
        "reason": "Paper figures require traceable data, export QA, and visual inspection.",
    },
    {
        "gate": "manuscript_consistency",
        "minimum_profile": "delivery",
        "applies": delivery_in(*PAPER_DELIVERIES),
        "reason": "Check numbers, terms, units, figures, tables, and citations together.",
    },
    {
        "gate": "word_omml_and_page_review",
        "minimum_profile": "delivery",
        "applies": delivery_in("word-only"),
        "reason": "Word formulas must be native OMML and every Word-rendered page reviewed.",
    },
    {
        "gate": "cumcm_latex_preflight",
        "minimum_profile": "delivery",
        "applies": delivery_in("cumcm-latex"),
        "reason": "CUMCM LaTeX delivery requires format audit and final PDF review.",
    },
]


def resolve(context: dict[str, Any]) -> dict[str, Any]:
    profile = context["workflow_profile"]
    level = PROFILE_ORDER[profile]
    required: list[dict[str, str]] = []
    deferred: list[dict[str, str]] = []
    not_applicable: list[dict[str, str]] = []
    for gate in GATES:
        decision = {"gate": gate["gate"], "reason": gate["reason"]}
        if not gate["applies"](context):
            not_applicable.append(decision)
        elif PROFILE_ORDER[gate["minimum_profile"]] <= level:
            required.append(decision)
        else:
            decision["required_from_profile"] = gate["minimum_profile"]
            deferred.append(decision)
    return {
        "schema_version": "1.0",
        "workflow_profile": profile,
        "task_family": context["task_family"],
        "features": sorted(context["features"]),
        "delivery_profile": context["delivery_profile"],
        "required_gate_count": len(required),
        "required_gates": required,
        "deferred_gates": deferred,
        "not_applicable_gates": not_applicable,
    }


def load_project_state(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    value = json.loads(path.expanduser().resolve().read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("project state must be a JSON object")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-state", type=Path)
    parser.add_argument(
        "--update-project-state",
        action="store_true",
        help="Persist --profile into the supplied project-state JSON after review.",
    )
    parser.add_argument("--profile", choices=tuple(PROFILE_ORDER))
    parser.add_argument(
        "--task-family",
        choices=(
            "general",
            "prediction",
            "classification",
            "clustering",
            "estimation",
            "evaluation",
            "optimization",
            "scheduling",
            "control",
            "simulation",
            "reconstruction",
            "mixed",
        ),
        default="general",
    )
    parser.add_argument("--feature", action="append", default=[])
    parser.add_argument(
        "--delivery-profile",
        choices=("word-only", "paper-bundle", "cumcm-latex", "code-only", "custom"),
    )
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        state = load_project_state(args.project_state)
        profile = args.profile or state.get("workflow_profile", "explore")
        delivery_profile = args.delivery_profile or state.get(
            "delivery_profile", "paper-bundle"
        )
        if profile not in PROFILE_ORDER:
            raise ValueError(f"invalid workflow profile: {profile!r}")
        if args.update_project_state:
            if args.project_state is None or args.profile is None:
                raise ValueError(
                    "--update-project-state requires --project-state and --profile"
                )
            state["workflow_profile"] = profile
            args.project_state.expanduser().resolve().write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        context = {
            "workflow_profile": profile,
            "task_family": args.task_family,
            "features": set(args.feature),
            "delivery_profile": delivery_profile,
        }
        result = resolve(context)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "issues": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
