---
name: math-modeling-solver
description: End-to-end mathematical modeling problem solver for competitions and applied projects. Use for problem decomposition, data auditing, model-family selection, executable Python or MATLAB solutions, robustness analysis, publication-grade quantitative plots and code-native modeling diagrams, argument-first competition-paper writing, reproducibility, and claim-to-evidence tracing. Also use when a modeling task asks what chart to use, requests paper-ready figures, multi-panel layouts, forecasting or optimization plots, sensitivity figures, Chinese scientific plotting, vector export, or figure QA.
---

# Math Modeling Solver

Turn a modeling prompt into a reproducible result and a defensible paper. Optimize for evidence, clarity, and contest time rather than method novelty alone.

## Non-Negotiable Rules

- Never invent data, execution results, metrics, citations, or chart conclusions.
- Label the run as <code>formal</code>, <code>demo</code>, or <code>blocked</code>. Formal runs may not silently replace missing data with synthetic data.
- Establish a simple baseline before adding model complexity.
- Fix the semantic contract before computation: define axes, signs, units, metric formulas, constraint meanings, and whether a quantity is observed, inferred, apparent, or causal.
- Diagnose score headroom and component-level gaps before tuning an optimizer.
- Remove hard-constraint violations from the action space; do not rely on penalty-only or post-hoc repair for illegal actions.
- Validate every search surrogate against the exact simulator before increasing its search budget.
- Do not promote a candidate from one favorable loss alone. Require task-specific structural or physical invariants and report effective support, coverage, and identifiability.
- Separate prediction or estimation quality from downstream decision quality; propagate upstream uncertainty through allocation, optimization, or correction stages.
- Do not call one trade-off point a Pareto front. State whether multi-objective coverage is adequate or limited.
- Keep training, validation, and test information separated; treat temporal and grouped data with structure-aware splits.
- Tie every important conclusion to a result file, table, figure, formula, or verified source.
- Generate quantitative figures from traceable data and code. Never use AI-generated imagery as empirical evidence.
- Give every figure one primary conclusion. Do not fill a canvas with redundant panels or decoration.
- Record units, assumptions, random seeds, software versions, commands, and input provenance.
- Report uncertainty, failure cases, and claim boundaries.

## Operating Workflow

1. Identify the requested scope, available data, time budget, implementation language, and delivery profile: <code>word-only</code>, <code>paper-bundle</code>, <code>code-only</code>, or an explicit custom contract.
2. Classify each sub-question and map dependencies between them.
3. Create or update the modeling workspace. For a new project, run:

       python scripts/init_modeling_project.py PROJECT_DIR --mode formal --questions N

4. Before modeling tabular data, run the executable audit and declare any known prediction roles:

       python scripts/audit_dataset.py INPUT.csv --target LABEL --time TIME --group ENTITY --split SPLIT --out-dir PROJECT_DIR/audit/dataset

   The script supports CSV, TSV, delimited TXT/DAT, Excel, and two-dimensional MAT variables. Review its JSON, CSV, and HTML outputs; automated flags are screening evidence, not automatic deletion rules. Do not claim that leakage is absent unless feature availability at prediction time is also documented.
5. Before comparing candidates, record the semantic contract, effective support, and task-specific state invariants. For scored optimization, compute the theoretical bound, executed baseline, reference gap, component gaps, and weighted sensitivity before tuning. Use <code>scripts/analyze_score_gap.py</code> only when its additive normalized-score assumption matches the real score contract.
6. For discrete-event search, scheduling, Beam Search, MPC, or learned policies, construct a hard-constraint action mask and compare the surrogate with the exact simulator for at least 50 consecutive steps using <code>scripts/check_transition_fidelity.py</code>. Do this before expanding search width, horizon, population, or training budget.
7. Register each optimization experiment with a hypothesis, primary metric, improvement threshold, run/runtime budget, feasibility/fidelity requirements, and stop rule. Use <code>scripts/register_experiment.py</code> where practical.
8. Before promoting a candidate, complete <code>assets/templates/candidate-validation-template.json</code> and run <code>scripts/audit_candidate_evidence.py</code>. A low residual, good cycle closure, high silhouette score, or improved cross-validation metric is insufficient when the reconstructed state, support, or downstream decision is invalid.
9. Advance through the five evidence gates in order:
   - Intake: problem contract and data audit are complete.
   - Method: candidates, baseline, feasibility probe, and selection rationale are recorded.
   - Computation: code actually ran and can be reproduced.
   - Evidence: baseline comparison, robustness evidence, and canonical numbers are frozen.
   - Manuscript: the argument, claims, figures, tables, terminology, units, and citations are consistent.
10. If an upstream assumption, dataset, method, parameter, score contract, constraint mask, or transition rule changes, mark downstream artifacts stale and rerun the affected gates.
11. Audit before delivery:

       python scripts/audit_modeling_project.py PROJECT_DIR

12. Deliver only the artifacts required by the delivery profile plus unresolved risks and the audit status. Do not present a failed gate as completed work.

## Human Decision Points

Pause for the user's decision when:

- two viable methods encode materially different assumptions or trade-offs;
- the selected method is about to replace a working baseline with a substantially more complex route;
- results are ready to be frozen as the canonical numbers used in the paper;
- missing real data would force a switch from formal to demo mode.

If the user is unavailable and time is limited, keep the baseline, document the assumption, and continue only where the choice is reversible.

## Reference Routing

- Rapid triage: read <code>references/problem-triage.md</code> and <code>references/task-family-router.md</code>.
- Model selection or upgrades: read <code>references/model-selection.md</code> and <code>references/when-to-upgrade-model-complexity.md</code>.
- Scored optimization or comparison with another result: read <code>references/score-gap-analysis.md</code>, then use <code>scripts/analyze_score_gap.py</code> when its score assumption applies.
- Discrete-event scheduling, Beam Search, MPC, or simulator-backed search: read <code>references/discrete-event-scheduling.md</code>, <code>references/hard-constraint-action-mask.md</code>, and <code>references/exact-simulation-contract.md</code>. Use <code>scripts/check_transition_fidelity.py</code> before increasing search budget.
- Optimization experiments or result promotion: read <code>references/experiment-budget-and-promotion.md</code> and <code>references/candidate-validation-contract.md</code>, then use <code>scripts/register_experiment.py</code>, <code>scripts/audit_candidate_evidence.py</code>, and <code>scripts/promote_validated_candidate.py</code> where practical.
- Reconstruction, registration, clustering, anomaly detection, multi-stage prediction-to-decision pipelines, or multi-objective claims: read <code>references/candidate-validation-contract.md</code>. Validate the physical or structural state, support coverage, semantic definitions, and downstream decision separately from the primary fit metric.
- MATLAB, Simulink, or MATLAB MCP work: read <code>references/matlab-native-workflow.md</code>. Keep the authoritative model and figures in MATLAB when that reduces fidelity risk or the user requests it.
- End-to-end work: read <code>references/evidence-gated-workflow.md</code> and <code>references/standard-workflow.md</code>.
- Data, leakage, or reproducibility: read <code>references/data-and-reproducibility.md</code>, then use <code>scripts/audit_dataset.py</code> for supported files.
- Validation, sensitivity, or uncertainty: read <code>references/validation-playbook.md</code>.
- Scientific figures, chart selection, multi-panel layouts, modeling diagrams, or export QA: read <code>references/modeling-figure-workflow.md</code>, then <code>references/figure-contract-and-qa.md</code>. Before delivery also read <code>references/figure-qa-checklist.md</code>.
- Code templates: read <code>references/algorithm-templates.md</code>, then inspect only the closest file under <code>assets/code/python/</code> or <code>assets/code/matlab/</code>.
- Combination models: read <code>references/advanced-model-combinations.md</code>.
- Paper planning or writing: read <code>references/argument-first-paper-writing.md</code>, <code>references/paper-writing.md</code>, and the templates under <code>assets/templates/</code>.
- Time-limited work: read <code>references/competition-timeline.md</code>.
- Prompt design: read <code>references/ai-prompt-patterns.md</code>.
- Skill maintenance or generalization testing on historical problems: read <code>references/blind-benchmarking.md</code>, then use <code>scripts/blind_modeling_benchmark.py</code>. Keep judge rubrics outside the evaluated agent context until responses are frozen.

## Figure Workflow

Use one of two routes and keep their evidence roles distinct.

### Quantitative route

Use for comparisons, distributions, forecasts, residuals, convergence, Pareto fronts, sensitivity, robustness, spatial/network results, and simulation trajectories.

1. State the one-sentence conclusion and the reader question.
2. Inspect variable types, sample sizes, grouping, uncertainty, units, and the baseline before selecting a chart.
3. Use the native backend selected for the modeling run. Python/Matplotlib and MATLAB are both valid when their figures satisfy the same traceability, statistics, export, and visual-QA contract. Do not force a cross-language handoff that risks changing authoritative results.
4. For Python, start from <code>assets/code/python/modeling_plotkit.py</code>. For MATLAB, follow <code>references/matlab-native-workflow.md</code> and use deterministic <code>exportgraphics</code> commands.
5. Render at final size, run programmatic QA, open the PNG preview, revise, then export vector and raster deliverables.

### Code-native diagram route

Use for problem structure, algorithm pipelines, layered architectures, feedback loops, and baseline-versus-proposed mechanisms.

1. Classify the argument as pipeline, layered system, closed loop, contrast, taxonomy, or decision flow.
2. Require module and relationship detail; an abstract alone is not enough for a defensible architecture.
3. Use flat vector structure, functional color, short labels, explicit arrows, and one visually dominant innovation.
4. Prefer editable SVG/PDF generated from code. Start from <code>assets/templates/modeling-diagram-spec-template.json</code> and use <code>scripts/build_modeling_diagram.py</code> for supported layouts.
5. Mark any AI-generated conceptual illustration as illustrative. Never place it in a quantitative evidence role.

### Figure bundle by delivery profile

For <code>paper-bundle</code>, deliver or record:

- a completed figure contract with conclusion, role, panel map, final size, backend, source data, statistics, and review risks;
- the generating script and deterministic command;
- source data or a traceable result artifact;
- SVG or PDF with editable text, plus a 300 dpi PNG preview;
- a grayscale preview when color carries categories;
- a QA JSON report and an actual visual inspection of the final-size preview.

Use <code>scripts/audit_figure_bundle.py</code> to validate a completed bundle. A successful save call is not visual QA.

For <code>word-only</code>, keep source data, generating code, and QA records in the workspace, but embed only the figures and tables necessary for the report in the final Word file. Do not create redundant public CSV/Excel attachments. For <code>code-only</code>, keep visual outputs limited to diagnostics needed to validate the implementation. A custom contract overrides these defaults when explicit.

## Result Lifecycle

Move successful results only through:

<code>exploratory → candidate → independently_validated → frozen → manuscript</code>

Use <code>rejected_infeasible</code>, <code>rejected_no_improvement</code>, or <code>rejected_fidelity_failure</code> as terminal states. A high score does not permit skipping feasibility, fidelity, structural validity, support adequacy, or independent validation. Freeze only canonical results approved for writing, and promote to manuscript only after the document actually contains the verified result and its evidence boundary.

## Required Outputs by Request Type

- Triage: sub-question map, task family, objectives, constraints, data needs, 2-3 candidates, baseline, and major risk.
- Model plan: assumptions, mathematical formulation, candidate comparison, baseline, feasibility probe, metrics, validation design, and fallback.
- Code: input contract, executable source, deterministic command, outputs, error checks, and reproducibility record.
- Results: baseline comparison, semantic definitions, effective support or coverage, task-specific structural checks, uncertainty or robustness evidence, limitations, and a claim-evidence map.
- Figure: one-sentence visual message, justified chart/diagram archetype, non-redundant panel map, source-data links, uncertainty/statistics, generating code, SVG/PDF + PNG preview, grayscale check when relevant, QA JSON, and final-size visual QA.
- Paper: one-sentence argument, section and paragraph jobs, terminology ledger, evidence-backed results, consistent figures/tables, limitations, and no unsupported claims.
- Word-only: one final DOCX containing the necessary verified tables and figures; retain code, source data, and QA records in the working directory without requiring them as separate submission files.
- Paper-bundle: manuscript, executable code, canonical data/results, complete figure bundle, and audit records.
- Code-only: executable source, input contract, deterministic command, tests, result summary, and only validation-essential diagnostics.

## Complexity Escalation Test

Add a component only when all are true:

1. The baseline has been executed.
2. Its failure is observable and named.
3. The added component directly addresses that failure.
4. The comparison protocol is fair.
5. Any surrogate has passed the exact-transition fidelity gate and all hard constraints are masked before search.
6. The candidate has declared structural or physical invariants, support requirements, and downstream validation appropriate to the claim.
7. The experiment has a registered improvement threshold, budget, and stop rule.
8. The remaining time supports independent validation.

Otherwise retain the baseline and improve data quality, formulation, diagnostics, or explanation first.

<!-- skill-provenance:v1;owner=YANG985-CMD;id=YANG985-CMD-MMS-2026-v8;path=SKILL.md;sha256=8bb3029b5c437eac5c89c901d14a74f2490dc8d8956cc2cefe17dc52ab8ef360;pub=0ofp8dKKJWMQK0LUC4dZDC8cynCRQlggy7cVeq7NfBo=;sig=AUDxfgevuCbWSZmHaqmwAFJL5Gek2EiM8OJt5RGlBPFAYogTEspEX2D6Oc_kUhv86pule6d20NGgLQaS1Ak8DA== -->
