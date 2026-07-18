# Experiment Budget and Promotion

Treat every model or optimizer change as a falsifiable experiment, not a tuning narrative.

## Register before running

Record:

- a concrete hypothesis and the mechanism it changes;
- one primary metric and executed baseline;
- direction and minimum meaningful improvement;
- maximum runs and runtime budget;
- feasibility and fidelity requirements;
- stopping condition and required artifact.

Example:

```text
python scripts/register_experiment.py planning/experiments.json create --id E01 --hypothesis "A mandatory-service mask removes voluntary idling" --metric score --direction max --baseline 55.2 --min-improvement 0.5 --max-runs 6 --max-runtime-minutes 30 --stop-condition "stop after six runs or a fidelity failure"
```

Record a run only after it produces an inspectable artifact:

```text
python scripts/register_experiment.py planning/experiments.json record --id E01 --value 57.1 --feasible --fidelity passed --artifact results/E01/run-1.json
```

## Status lifecycle

Successful results advance only in this order:

```text
exploratory -> candidate -> independently_validated -> frozen -> manuscript
```

Terminal rejection states are:

- `rejected_infeasible` for any hard-constraint failure;
- `rejected_no_improvement` when the registered budget ends below threshold;
- `rejected_fidelity_failure` when surrogate and exact dynamics disagree.

Promote with independent evidence:

```text
python scripts/promote_validated_candidate.py planning/experiments.json --id E01 --to independently_validated --evidence results/E01/independent-validation.json
```

Promotion to `frozen` additionally requires a named approver. Promotion to `manuscript` requires an actual manuscript artifact.

## Stop rules

- Stop immediately on infeasibility or transition-fidelity failure.
- Stop at the registered run/runtime budget when improvement is below threshold.
- Do not restart an exhausted experiment by renaming it; register a new mechanism and explain what changed.
- Compare only runs with the same score contract, scenario set, seed policy, and compute budget.
- Report all registered runs or a predeclared aggregation; do not select only the best favorable seed.
