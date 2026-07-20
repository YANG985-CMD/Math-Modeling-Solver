---
name: audit-modeling-evidence
description: Audit existing mathematical modeling data, experiments, results, constraints, reproducibility, and claim-to-evidence links. Use when the primary request is to check or validate an existing modeling project rather than solve a complete new problem.
---

# Audit Modeling Evidence

Audit an existing modeling project without silently repairing, rerunning, or promoting unsupported claims. Return the smallest defensible repair and a clear status: `pass`, `warn`, or `blocked`.

## Audit workflow

1. Identify the source-of-truth files, active subquestion, data mode, claimed result status, and requested audit scope.
2. Choose only the applicable lane:
   - dataset and leakage;
   - experiment budget and candidate promotion;
   - simulator or decision-trace fidelity;
   - project, reproducibility, and claim consistency.
3. Run the smallest deterministic check first. Preserve input hashes, commands, environment, and output paths.
4. Distinguish `observed`, `inferred`, `diagnostic-only`, `paper-ready`, and `blocked` evidence. Do not convert a warning into a pass by rewriting the claim.
5. Report failed checks with file, field or row, observed value, expected condition, and the smallest repair. Mark downstream artifacts stale when an upstream input or assumption changed.

## Script routing

- Dataset schema, missingness, outliers, units, target copies, temporal or group leakage: `scripts/audit_dataset.py`.
- Score upper bounds, reference gaps, component gaps, and weighted sensitivity: `scripts/analyze_score_gap.py`, only when the declared additive normalized-score contract applies.
- Experiment registration, runtime capture, cumulative budgets, and stop rules: `scripts/register_experiment.py` and `scripts/run_experiment.py`.
- Candidate evidence, structural checks, support, robustness, and promotion: `scripts/audit_candidate_evidence.py` and `scripts/promote_validated_candidate.py`.
- Hard-constraint decisions, first divergence, and surrogate/exact transition checks: `scripts/audit_decision_trace.py` and `scripts/check_transition_fidelity.py`.
- MATLAB/Python scalar, array, JSON, and Chinese-path round trips: `scripts/preflight_matlab_python_bridge.py`.
- Whole-project artifact, terminology, result, and manuscript consistency: `scripts/audit_modeling_project.py`.
- Gate applicability and deferred checks: `scripts/resolve_required_gates.py`.

## Conditional rules

- Use hard-constraint action masks for constructive search, scheduling, Beam Search, MPC, or learned policies when illegal actions can enter the search space. Solver-native LP/MILP/NLP constraints do not need to be rewritten as action masks.
- Compare a surrogate with an exact simulator using predeclared coverage and independent cases. Use the repository's 50-step default only when the horizon and state space make it meaningful; otherwise document a task-specific coverage rule.
- Separate reproducibility, sensitivity, robustness, and generalization. Same-instance replay is not evidence of transfer.
- Do not call one trade-off point a Pareto front. Report coverage and limitations.

## Required audit output

Return:

- current lock and source-of-truth files;
- checks run and deterministic commands;
- pass/warn/blocked findings with evidence locations;
- stale or affected downstream artifacts;
- paper-ready versus diagnostic-only claims;
- the smallest next repair and its stop condition.

Read only the reference needed by the lane: `references/data-and-reproducibility.md`, `references/candidate-validation-contract.md`, `references/experiment-budget-and-promotion.md`, `references/exact-simulation-contract.md`, `references/discrete-event-scheduling.md`, `references/hard-constraint-action-mask.md`, `references/score-gap-analysis.md`, `references/matlab-native-workflow.md`, or `references/validation-playbook.md`.
