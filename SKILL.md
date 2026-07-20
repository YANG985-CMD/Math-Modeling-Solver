---
name: math-modeling-solver
description: Solve end-to-end mathematical modeling competition or applied modeling tasks requiring problem decomposition, model selection, executable Python or MATLAB computation, validation, and coordinated delivery. Use when the primary request is a complete modeling solution or requires coordination across multiple modeling stages.
---

# Math Modeling Solver

Act as the end-to-end modeling orchestrator. Optimize for a defensible answer that can be executed, checked, and explained within the available contest time.

## Scope and routing

- Keep this Skill active for complete problems: triage, model choice, code, validation, and integrated paper or result delivery.
- Route an evidence-only request to `audit-modeling-evidence` when the user already has data, runs, results, or a project to check.
- Route a figure-only request to `build-modeling-figures` when the primary deliverable is a quantitative plot, diagram, or figure QA package.
- Route a CUMCM formatting or submission-only request to `deliver-cumcm-paper`.
- If a specialist is not installed, use the corresponding references and scripts bundled in this repository.
- Do not split a single subquestion into independent handoffs when that would lose variables, units, constraints, or evidence links.

## Universal rules

- Never invent data, execution results, metrics, citations, or chart conclusions.
- Declare the data mode: `formal` for real traceable data or `demo` for explicitly labeled synthetic data. Use a `blocked` gate outcome when a required input or authorization is missing.
- Define the problem contract before computation: objectives, subquestions, inputs, variables, units, constraints, assumptions, and deliverables.
- Establish and execute a simple baseline before adding model complexity.
- Keep training, validation, and test information separated; use time-, group-, or structure-aware splits when required.
- Record input provenance, commands, parameters, seeds, software versions, and output paths for formal runs.
- Tie every important claim to a result file, table, figure, formula, or verified source.
- Report uncertainty, failure cases, unresolved risks, and claim boundaries.

## State model

Keep these concepts orthogonal:

- `data_mode`: `formal` or `demo`.
- `workflow_stage`: `explore`, `validate`, or `deliver`.
- `result_status`: `draft`, `validated`, `frozen`, or `manuscript`.
- `delivery_profile`: `paper-bundle`, `cumcm-latex`, `code-only`, or `custom`.

Evidence gates (`Intake`, `Method`, `Computation`, `Evidence`, `Manuscript`) return `pass`, `warn`, or `blocked`; they are checks, not additional user-managed states. A blocked gate remains blocked until the required artifact is repaired or the claim is downgraded.

## Core workflow

1. Lock the problem statement, attachments, time budget, implementation language, data mode, workflow stage, and delivery profile.
2. Decompose the statement into subquestions and map dependencies between them.
3. Classify each subquestion, choose a conservative baseline, define its variables and validation, and record why more complex candidates may be needed.
4. Create or update the workspace. For a new project, run:

       python scripts/init_modeling_project.py PROJECT_DIR --mode formal --workflow-stage explore --questions N

5. Run only the checks required by the current stage. Use `scripts/resolve_required_gates.py` to record required, deferred, and inapplicable gates.
6. Execute the baseline and candidates with reproducible commands. Keep exploratory, validated, frozen, and manuscript claims separate.
7. Promote only results with fair comparison, task-appropriate validation, robustness evidence, and a clear evidence link. Freeze canonical numbers before writing.
8. Audit the project before delivery:

       python scripts/audit_modeling_project.py PROJECT_DIR

   Add `--with-evidence-bundle` when the project uses the result/run/figure registries.

9. Deliver only the requested artifacts plus audit status and unresolved risks. If a required input is missing, return `blocked` instead of silently switching to synthetic data.

## Conditional routing

- Data schemas, leakage, missingness, units, and split risks: read `references/data-and-reproducibility.md`, then use `scripts/audit_dataset.py`.
- Reusable algorithm baselines: read `references/algorithm-library.md` and inspect `assets/code/python/modeling_algorithms/` before copying a specialized template.
- Claim/result/run/figure registries, real-data PoCs, frozen hashes, and human review items: read `references/evidence-registry-contract.md`, then use `scripts/init_evidence_bundle.py` and `scripts/audit_evidence_bundle.py`.
- Model family selection and complexity upgrades: read `references/model-selection.md`, `references/when-to-upgrade-model-complexity.md`, and `references/failure-to-method-router.md`.
- Validation, sensitivity, and uncertainty: read `references/validation-playbook.md`.
- Optimization experiments, candidate promotion, action masks, score gaps, exact simulation, or MATLAB bridges: route to `audit-modeling-evidence` or read only the applicable specialized reference.
- Figures and diagrams: route to `build-modeling-figures` instead of loading the complete figure workflow for a figure-only task.
- Paper planning: read `references/argument-first-paper-writing.md` and `references/paper-writing.md`; route CUMCM LaTeX and PDF preflight to `deliver-cumcm-paper`.
- Historical-problem or architecture testing: read `references/blind-benchmarking.md` and keep rubrics outside the evaluated agent context until responses are frozen.

## Required outputs

- Triage: subquestion map, task family, objectives, constraints, data needs, baseline, candidates, and major risks.
- Model plan: assumptions, mathematical formulation, candidate rationale, feasibility probe, metrics, validation, robustness, and fallback.
- Code: input contract, executable source, deterministic command, outputs, error checks, and provenance record.
- Results: baseline comparison, diagnostics, uncertainty or robustness evidence, limitations, and a claim-to-evidence map.
- Integrated paper: a one-sentence argument, frozen numbers, consistent terminology, evidence-backed figures and tables, and explicit limitations.

## Reusable assets

- Start common baselines from `assets/code/python/modeling_algorithms/`; it exposes validated entropy weights, TOPSIS, GM(1,1), linear programming, Monte Carlo, bootstrap, and rolling-origin APIs with intermediate diagnostics. Treat the older metaheuristic files under `assets/code/python/` as experimental templates until they pass task-specific checks.
- For results that will enter a paper or be reused across runs, initialize the evidence registries with `python scripts/init_evidence_bundle.py PROJECT_DIR` and audit them with `python scripts/audit_evidence_bundle.py PROJECT_DIR`.

## Complexity escalation

Add a component only when the baseline has run, its failure is observable and named, the component directly addresses that failure, the comparison is fair, and remaining time supports validation. Apply specialized rules such as hard-constraint action masks or surrogate fidelity checks only when the task family requires them; do not impose them on unrelated regression, ranking, geometry, or plotting work.
