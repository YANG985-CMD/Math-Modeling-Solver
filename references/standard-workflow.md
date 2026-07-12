# Standard Workflow

Use this concise sequence for competition execution. For gate evidence and invalidation rules, pair it with <code>evidence-gated-workflow.md</code>.

## 1. Frame

- Restate each question as an input-output contract.
- Draw dependencies between sub-questions.
- List deliverables, units, constraints, assumptions, and available data.
- Select formal, demo, or blocked mode.

## 2. Audit Data

- Verify provenance, schema, missingness, outliers, and units.
- Choose temporal, grouped, spatial, or random splits that match dependence.
- Identify leakage and information unavailable at decision time.

## 3. Compare Methods

- Establish a transparent baseline.
- Compare 2-3 candidates on assumption fit, data demand, interpretability, runtime, and validation burden.
- Run a minimal feasibility probe.
- Lock the primary metric before final evaluation.

## 4. Execute

- Implement the baseline first.
- Save commands, seeds, versions, parameters, source paths, and output paths.
- Capture errors and fixes.
- Add complexity only after a measurable baseline failure.

## 5. Validate

- Check feasibility, units, and limiting cases.
- Compare fairly with the baseline.
- Add task-specific out-of-sample, sensitivity, uncertainty, or perturbation evidence.
- Inspect failure cases and state the validated scope.

## 6. Freeze Evidence

- Ask for approval of the canonical result set.
- Store paper numbers in <code>results/frozen-results.json</code>.
- Map each headline claim to an artifact in the claim-evidence ledger.

## 7. Write and Audit

- Explain why the model fits before describing implementation detail.
- Generate tables and figures from verified artifacts.
- Cross-check notation, units, references, and frozen numbers.
- Run the audit script and resolve failed gates before delivery.
