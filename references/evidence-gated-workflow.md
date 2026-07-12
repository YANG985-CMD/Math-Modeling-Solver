# Evidence-Gated Workflow

Use this protocol for end-to-end projects. A stage is not complete because prose exists; it is complete only when its gate has inspectable evidence.

## Run Modes

- Formal: real inputs and real execution are required. Missing data blocks empirical claims.
- Demo: synthetic or example data are allowed, but every output must be visibly labeled as illustrative.
- Blocked: preserve the plan and list the exact missing inputs without fabricating results.

## Workspace Contract

The initialization script creates:

- <code>input/</code>: immutable copies or links to source data
- <code>planning/</code>: problem contract, method decision, and data audit
- <code>src/</code>: executable analysis and model code
- <code>results/tables/</code> and <code>results/figures/</code>: generated evidence
- <code>results/frozen-results.json</code>: canonical numbers approved for writing
- <code>paper/</code>: manuscript source
- <code>audit/</code>: reproducibility, claim ledger, gate state, and audit reports

Do not manually copy final numbers into several files. Freeze them once and derive paper tables from the canonical record when practical.

## Gate A — Intake

Required evidence:

- deliverables and sub-questions are explicit;
- objectives, constraints, units, and assumptions are recorded;
- dependencies between sub-questions are identified;
- every input has provenance, format, and quality notes;
- missing values, outliers, duplicates, impossible ranges, and leakage risks are assessed.

Failure action: switch to blocked mode or request data. Demo mode requires explicit consent.

## Gate B — Method

Required evidence for each sub-question:

- at least one simple baseline;
- a short candidate comparison based on assumptions, data, interpretability, runtime, and validation burden;
- a minimal feasibility probe or hand-check;
- chosen method and rejection reasons;
- metrics and split strategy decided before looking at final test performance.

Human checkpoint: confirm the selected route when viable candidates imply different interpretations or trade-offs.

### Maker–Critic Check

For full or high-stakes work, use one bounded review loop:

1. The maker proposes the formulation and feasibility evidence.
2. The critic tries to falsify assumptions, find leakage, expose missing constraints, and challenge the baseline comparison.
3. The maker either revises the route or records why the criticism does not change it.

Allow at most two review cycles without new evidence. Repeated opinions are not progress.

## Gate C — Computation

Required evidence:

- executable source code;
- exact run command;
- environment and dependency versions;
- random seed policy;
- input and output file paths;
- captured errors and resolution notes;
- generated tables, figures, or metrics.

Failure action: report the error and keep the gate open. Do not narrate expected output as observed output.

## Gate D — Evidence

Required evidence:

- fair comparison against the baseline;
- task-appropriate sensitivity, perturbation, uncertainty, or out-of-sample checks;
- stability across relevant seeds, folds, scenarios, or parameter ranges;
- limitations and known failure regions;
- every headline claim mapped in <code>audit/claim-evidence-ledger.csv</code>;
- approved numbers stored in <code>results/frozen-results.json</code>.
- every quantitative figure has a contract linking its message, panels, source data, script, statistics, exports, and final-size QA;
- AI-generated or conceptual imagery is excluded from empirical evidence roles.

Human checkpoint: approve the canonical result set before final paper writing.

Before freezing, run a second critic pass focused on infeasible outputs, cherry-picked seeds or scenarios, uncertainty, and conclusions that exceed the tested scope.

## Gate E — Manuscript

Required evidence:

- formulas match implemented logic;
- a one-sentence paper argument, evidence boundary, and section jobs are approved;
- a terminology ledger fixes model names, abbreviations, symbols, metrics, and units;
- symbols and units are defined and consistent;
- every figure and table is referenced and interpreted;
- numbers match the frozen result set;
- claims stay within the validated scope;
- citations are verified rather than guessed;
- abstract, conclusion, and body tell the same quantitative story.

## Invalidation Rule

Track upstream changes instead of polishing stale outputs:

- Problem or data change invalidates Method through Manuscript.
- Method or parameter-policy change invalidates Computation through Manuscript.
- Code or environment change invalidates Evidence and Manuscript.
- Frozen-number change invalidates Manuscript.

When invalidated, preserve prior artifacts for traceability, mark them stale, and rerun the smallest affected suffix of the workflow.

## Recovery Strategy

1. Retry only after identifying a concrete failure cause.
2. Limit repeated blind tuning.
3. Fall back to the last passing baseline.
4. Reduce scope before weakening evidence standards.
5. Record unresolved risks in the final handoff.
