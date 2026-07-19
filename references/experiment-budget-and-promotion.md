# Experiment Budget and Promotion

Treat every model or optimizer change as a falsifiable experiment, not a tuning narrative.

## Register before running

Record:

- a concrete hypothesis and the mechanism it changes;
- one primary metric and executed baseline;
- direction and minimum meaningful improvement;
- maximum runs and runtime budget;
- a per-experiment candidate-evaluation budget and one cumulative budget for the whole experiment family;
- the parent experiment, family name, and what adaptive search choices may bias later comparisons;
- feasibility and fidelity requirements;
- stopping condition and required artifact.

Example:

```text
python scripts/register_experiment.py planning/experiments.json create --id E01 --experiment-family PBS-Q2 --candidate-budget 1200 --cumulative-candidate-budget 5000 --adaptive-search-bias-notes "Guard positions are selected only from training traces" --hypothesis "A mandatory-service mask removes voluntary idling" --metric score --direction max --baseline 55.2 --min-improvement 0.5 --max-runs 6 --max-runtime-minutes 30 --stop-condition "stop after six runs or a fidelity failure"
```

Record a run only after it produces an inspectable artifact:

```text
python scripts/register_experiment.py planning/experiments.json record --id E01 --value 57.1 --feasible --fidelity passed --candidates-evaluated 200 --runtime-minutes 4.8 --artifact results/E01/run-1.json
```

The artifact must already exist and remain inside the project. A child experiment must name `--parent-experiment` and stay in the same family. Do not reset the apparent search budget by creating new experiment IDs: report both the local experiment budget and the cumulative family budget.

## Status lifecycle

Successful results advance only in this order:

```text
exploratory -> candidate -> independently_validated -> frozen -> manuscript
```

Terminal rejection states are:

- `rejected_infeasible` for any hard-constraint failure;
- `rejected_no_improvement` when the registered budget ends below threshold;
- `rejected_fidelity_failure` when surrogate and exact dynamics disagree.

Promote with independent evidence. The JSON must follow
`assets/templates/candidate-validation-template.json` and pass
`scripts/audit_candidate_evidence.py`; a bare `{"status":"passed"}` file is not
validation evidence:

```text
python scripts/promote_validated_candidate.py planning/experiments.json --id E01 --to independently_validated --evidence results/E01/independent-validation.json
```

Promotion to `frozen` additionally requires a named approver. Promotion to `manuscript` requires an actual manuscript artifact.

The structured validation report must align with the experiment registry's
metric name, direction, baseline, and minimum improvement. It also records
semantic definitions, effective support, task-specific structural checks,
robustness, and conditional multi-objective or pipeline evidence. See
`candidate-validation-contract.md`.

## Stop rules

- Stop immediately on infeasibility or transition-fidelity failure.
- Stop at the registered run/runtime budget when improvement is below threshold.
- Do not restart an exhausted experiment by renaming it; register a new mechanism and explain what changed.
- Compare only runs with the same score contract, scenario set, seed policy, and compute budget.
- Report all registered runs or a predeclared aggregation; do not select only the best favorable seed.
- Count every adaptively inspected candidate in the family budget, including discarded pilots that influenced later guard positions, features, or hyperparameters.
