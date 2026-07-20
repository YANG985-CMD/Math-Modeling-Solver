# Standard Workflow

Use this concise sequence for competition execution. For gate evidence and invalidation rules, pair it with <code>evidence-gated-workflow.md</code>.

## 1. Frame

- Restate each question as an input-output contract.
- Draw dependencies between sub-questions.
- List deliverables, units, constraints, assumptions, and available data.
- Select `formal` or `demo` data mode; use a blocked gate status when required inputs are missing.
- Select `explore`, `validate`, or `deliver` workflow stage.
- Select paper-bundle, cumcm-latex, code-only, or a custom delivery profile.

## 2. Audit Data

- Verify provenance, schema, missingness, outliers, and units.
- Choose temporal, grouped, spatial, or random splits that match dependence.
- Identify leakage and information unavailable at decision time.

## 3. Compare Methods

- Establish a transparent baseline.
- For scored optimization, quantify theoretical headroom, reference gap, component gaps, and weighted sensitivity.
- Compare 2-3 candidates on assumption fit, data demand, interpretability, runtime, and validation burden.
- Run a minimal feasibility probe.
- Lock the primary metric before final evaluation.

## 4. Execute

- Implement the baseline first.
- Save commands, seeds, versions, parameters, source paths, and output paths.
- Capture errors and fixes.
- Add complexity only after a measurable baseline failure.
- For constructive or policy search, mask illegal actions. For surrogate-backed search, pass a predeclared exact-transition coverage rule before expanding the budget; use 50 consecutive steps only when it meaningfully covers the horizon.
- Register the hypothesis, minimum improvement, run/runtime budget, and stop condition for each tuning campaign.

## 5. Validate

- Check feasibility, units, and limiting cases.
- Compare fairly with the baseline.
- Add task-specific out-of-sample, sensitivity, uncertainty, or perturbation evidence.
- Inspect failure cases and state the validated scope.

## 6. Freeze Evidence

- Ask for approval of the canonical result set.
- Require the result to advance from candidate through independent validation before freezing.
- Store paper numbers in <code>results/frozen-results.json</code>.
- Map each headline claim to an artifact in the claim-evidence ledger.

## 7. Write and Audit

- Explain why the model fits before describing implementation detail.
- Generate tables and figures from verified artifacts.
- Cross-check notation, units, references, and frozen numbers.
- Run the audit script and resolve failed gates before delivery.
- Package only the requested delivery profile and keep all supporting evidence in the workspace.
