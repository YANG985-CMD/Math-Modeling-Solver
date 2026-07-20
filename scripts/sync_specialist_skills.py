#!/usr/bin/env python3
"""Synchronize self-contained specialist Skill resources from root sources."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SPECIALIST_SOURCES: dict[str, tuple[str, ...]] = {
    "audit-modeling-evidence": (
        "scripts/analyze_score_gap.py",
        "scripts/audit_candidate_evidence.py",
        "scripts/audit_dataset.py",
        "scripts/audit_decision_trace.py",
        "scripts/audit_modeling_project.py",
        "scripts/check_transition_fidelity.py",
        "scripts/preflight_matlab_python_bridge.py",
        "scripts/promote_validated_candidate.py",
        "scripts/register_experiment.py",
        "scripts/resolve_required_gates.py",
        "scripts/run_experiment.py",
        "references/candidate-validation-contract.md",
        "references/data-and-reproducibility.md",
        "references/discrete-event-scheduling.md",
        "references/evidence-gated-workflow.md",
        "references/exact-simulation-contract.md",
        "references/experiment-budget-and-promotion.md",
        "references/hard-constraint-action-mask.md",
        "references/matlab-native-workflow.md",
        "references/score-gap-analysis.md",
        "references/validation-playbook.md",
        "assets/templates/candidate-validation-template.json",
        "assets/templates/claim-evidence-ledger-template.csv",
        "assets/templates/decision-trace-template.json",
        "assets/templates/reproducibility-manifest-template.json",
    ),
    "build-modeling-figures": (
        "scripts/audit_figure_bundle.py",
        "scripts/build_modeling_diagram.py",
        "references/modeling-figure-workflow.md",
        "references/figure-contract-and-qa.md",
        "references/figure-qa-checklist.md",
        "assets/code/python/modeling_plotkit.py",
        "assets/code/python/demo_modeling_figure.py",
        "assets/templates/figure-contract-template.json",
        "assets/templates/modeling-diagram-spec-template.json",
    ),
    "deliver-cumcm-paper": (
        "scripts/audit_cumcm_latex.py",
        "scripts/build_cumcm_latex.py",
        "scripts/render_frozen_results.py",
        "references/argument-first-paper-writing.md",
        "references/paper-writing.md",
        "references/cumcm-2026-latex.md",
        "references/competition-timeline.md",
        "assets/latex/cumcm-2026/paper.tex",
        "assets/templates/manuscript-contract-template.json",
        "assets/templates/paper-outline-template.md",
        "assets/templates/terminology-ledger-template.csv",
    ),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synchronize(check: bool) -> list[str]:
    drift: list[str] = []
    for skill, relative_paths in SPECIALIST_SOURCES.items():
        for relative in relative_paths:
            source = ROOT / relative
            destination = ROOT / skill / relative
            if not source.is_file():
                drift.append(f"missing source: {relative}")
                continue
            if destination.is_file() and digest(source) == digest(destination):
                continue
            if check:
                drift.append(f"out of sync: {skill}/{relative}")
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            print(f"synced {skill}/{relative}")
    return drift


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize specialist Skill resources with root canonical files."
    )
    parser.add_argument(
        "--check", action="store_true", help="Report drift without changing files."
    )
    args = parser.parse_args()
    drift = synchronize(check=args.check)
    if drift:
        for item in drift:
            print(item)
        return 1
    print("specialist resources are synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
