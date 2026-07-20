---
name: math-modeling-solver
description: End-to-end mathematical modeling problem solver for competitions and applied projects. Use for problem decomposition, data auditing, model-family selection, executable Python or MATLAB solutions, robustness analysis, publication-grade quantitative plots and code-native modeling diagrams, argument-first competition-paper writing, reproducibility, claim-to-evidence tracing, Word reports with native OMML formulas, and CUMCM LaTeX paper production or format preflight. Also use when a modeling task asks what chart to use, requests paper-ready figures, multi-panel layouts, forecasting or optimization plots, sensitivity figures, Chinese scientific plotting, vector export, or figure QA.
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
- Keep reproducibility, sensitivity, robustness, and generalization as separate claims with separate evidence. A same-instance replay or sweep is not proof of transfer.
- Declare hand-selected positions, action sequences, and case-tuned schedules as instance-specific unless selection-free cases validate a reusable policy.
- Count inspected candidates across the whole experiment family. Record parent experiments and adaptive-search choices instead of resetting the apparent budget with a new experiment ID.
- Separate prediction or estimation quality from downstream decision quality; propagate upstream uncertainty through allocation, optimization, or correction stages.
- Do not call one trade-off point a Pareto front. State whether multi-objective coverage is adequate or limited.
- Keep training, validation, and test information separated; treat temporal and grouped data with structure-aware splits.
- Tie every important conclusion to a result file, table, figure, formula, or verified source.
- Generate quantitative figures from traceable data and code. Never use AI-generated imagery as empirical evidence.
- Give every figure one primary conclusion. Do not fill a canvas with redundant panels or decoration.
- Record units, assumptions, random seeds, software versions, commands, and input provenance.
- Report uncertainty, failure cases, and claim boundaries.
- For Word reports, convert LaTeX math through Pandoc to native OMML, verify `m:oMath`, render with Microsoft Word, and inspect every page. Never downgrade formulas to text or screenshots.

## Workflow Profiles

- Use <code>explore</code> while understanding the problem and finding a first feasible baseline. Require the semantic contract, executable baseline, inspectable artifacts, data audit when applicable, and hard constraints for decision problems. Defer promotion and manuscript gates.
- Use <code>candidate</code> only for the best one or two mechanisms. Add fair comparison, experiment-family budget, exact validation, sensitivity, robustness, and only the conditional fidelity, trace, generalization, multi-objective, pipeline, or bridge gates that apply.
- Use <code>delivery</code> after canonical numbers are approved. Add result freezing, claim-evidence consistency, figure QA, manuscript checks, and the selected Word or LaTeX delivery gate.

Resolve required, deferred, and inapplicable gates with <code>scripts/resolve_required_gates.py</code>. The data truth label <code>formal</code>/<code>demo</code>/<code>blocked</code> is independent of workflow profile and must not be used as a workload switch.

## Operating Workflow

1. Identify the requested scope, available data, time budget, implementation language, workflow profile, and delivery profile: <code>word-only</code>, <code>paper-bundle</code>, <code>cumcm-latex</code>, <code>code-only</code>, or an explicit custom contract.
2. Classify each sub-question and map dependencies between them.
3. Create or update the modeling workspace. For a new project, run:

       python scripts/init_modeling_project.py PROJECT_DIR --mode formal --workflow-profile explore --questions N

   Resolve the applicable gates for the task family and method features before loading detailed references.

4. Before modeling tabular data, run the executable audit and declare any known prediction roles:

       python scripts/audit_dataset.py INPUT.csv --target LABEL --time TIME --group ENTITY --split SPLIT --out-dir PROJECT_DIR/audit/dataset

   The script supports CSV, TSV, delimited TXT/DAT, Excel, and two-dimensional MAT variables. Review its JSON, CSV, and HTML outputs; automated flags are screening evidence, not automatic deletion rules. Do not claim that leakage is absent unless feature availability at prediction time is also documented.
5. Before comparing candidates, record the semantic contract, effective support, and task-specific state invariants. For scored optimization, compute the theoretical bound, executed baseline, reference gap, component gaps, and weighted sensitivity before tuning. Use <code>scripts/analyze_score_gap.py</code> only when its additive normalized-score assumption matches the real score contract.
6. For discrete-event search, scheduling, Beam Search, MPC, or learned policies, construct a hard-constraint action mask and compare the surrogate with the exact simulator for at least 50 consecutive steps using <code>scripts/check_transition_fidelity.py</code>. Do this before expanding search width, horizon, population, or training budget.
7. Register each optimization experiment with a hypothesis, primary metric, improvement threshold, local run/runtime/candidate budget, cumulative experiment-family budget, parent experiment, adaptive-search-bias note, feasibility/fidelity requirements, and stop rule. Use <code>scripts/register_experiment.py</code>; after registration, prefer <code>scripts/run_experiment.py</code> to capture the command, runtime, logs, result hash, candidate count, environment, and registry update automatically.
8. Before promoting a candidate, complete <code>assets/templates/candidate-validation-template.json</code> and run <code>scripts/audit_candidate_evidence.py</code>. Distinguish reproducibility, sensitivity, robustness, and generalization; declare instance-specific schedules and validation independence. A low residual, good cycle closure, high silhouette score, or improved cross-validation metric is insufficient when the reconstructed state, support, or downstream decision is invalid.
9. Advance through the five evidence gates in order:
   - Intake: problem contract and data audit are complete.
   - Method: candidates, baseline, feasibility probe, and selection rationale are recorded.
   - Computation: code actually ran and can be reproduced.
   - Evidence: baseline comparison, robustness evidence, and canonical numbers are frozen.
   - Manuscript: the argument, claims, figures, tables, terminology, units, and citations are consistent.
10. If an upstream assumption, dataset, method, parameter, score contract, constraint mask, or transition rule changes, mark downstream artifacts stale and rerun the affected gates.
11. Audit before delivery:

       python scripts/audit_modeling_project.py PROJECT_DIR

12. Generate manuscript numbers and tables from <code>results/frozen-results.json</code> rather than retyping them. For Word delivery, follow <code>references/word-omml-delivery.md</code> and pass the native-formula plus page-review audit.
13. Deliver only the artifacts required by the delivery profile plus unresolved risks and the audit status. Do not present a failed gate as completed work.

## Human Decision Points

Pause for the user's decision when:

- two viable methods encode materially different assumptions or trade-offs;
- the selected method is about to replace a working baseline with a substantially more complex route;
- results are ready to be frozen as the canonical numbers used in the paper;
- missing real data would force a switch from formal to demo mode.

If the user is unavailable and time is limited, keep the baseline, document the assumption, and continue only where the choice is reversible.

## Reference Routing

- Rapid triage: read <code>references/problem-triage.md</code> and <code>references/task-family-router.md</code>.
- Model selection or upgrades: read <code>references/model-selection.md</code>, <code>references/when-to-upgrade-model-complexity.md</code>, and <code>references/failure-to-method-router.md</code> after an executed baseline exposes a named failure.
- Workflow depth or gate applicability: run <code>scripts/resolve_required_gates.py</code> and load only the references for required gates. Do not run delivery gates during exploration.
- Scored optimization or comparison with another result: read <code>references/score-gap-analysis.md</code>, then use <code>scripts/analyze_score_gap.py</code> when its score assumption applies.
- Discrete-event scheduling, Beam Search, MPC, or simulator-backed search: read <code>references/discrete-event-scheduling.md</code>, <code>references/hard-constraint-action-mask.md</code>, and <code>references/exact-simulation-contract.md</code>. Use <code>scripts/check_transition_fidelity.py</code> before increasing search budget.
- Optimization experiments or result promotion: read <code>references/experiment-budget-and-promotion.md</code> and <code>references/candidate-validation-contract.md</code>, then use <code>scripts/register_experiment.py</code>, <code>scripts/audit_candidate_evidence.py</code>, and <code>scripts/promote_validated_candidate.py</code> where practical.
- Reconstruction, registration, clustering, anomaly detection, multi-stage prediction-to-decision pipelines, or multi-objective claims: read <code>references/candidate-validation-contract.md</code>. Validate the physical or structural state, support coverage, semantic definitions, and downstream decision separately from the primary fit metric.
- MATLAB, Simulink, or MATLAB MCP work: read <code>references/matlab-native-workflow.md</code>. Keep the authoritative model and figures in MATLAB when that reduces fidelity risk or the user requests it.
- Mixed MATLAB-Python computation: define the backend contract in <code>references/matlab-native-workflow.md</code> and run <code>scripts/preflight_matlab_python_bridge.py</code> before formal search. For path-dependent decisions, start from <code>assets/templates/decision-trace-template.json</code> and run <code>scripts/audit_decision_trace.py</code>.
- End-to-end work: read <code>references/evidence-gated-workflow.md</code> and <code>references/standard-workflow.md</code>.
- Data, leakage, or reproducibility: read <code>references/data-and-reproducibility.md</code>, then use <code>scripts/audit_dataset.py</code> for supported files.
- Validation, sensitivity, or uncertainty: read <code>references/validation-playbook.md</code>.
- Scientific figures, chart selection, multi-panel layouts, modeling diagrams, or export QA: read <code>references/modeling-figure-workflow.md</code>, then <code>references/figure-contract-and-qa.md</code>. Before delivery also read <code>references/figure-qa-checklist.md</code>.
- Code templates: read <code>references/algorithm-templates.md</code>, then inspect only the closest file under <code>assets/code/python/</code> or <code>assets/code/matlab/</code>.
- Combination models: read <code>references/advanced-model-combinations.md</code>.
- Paper planning or writing: read <code>references/argument-first-paper-writing.md</code>, <code>references/paper-writing.md</code>, and the templates under <code>assets/templates/</code>.
- Word reports: read <code>references/word-omml-delivery.md</code>. Generate frozen-number blocks with <code>scripts/render_frozen_results.py</code>, build equations through Pandoc, and audit the DOCX with <code>scripts/audit_word_delivery.py</code> after Word rendering and page-by-page inspection.
- CUMCM LaTeX formatting or submission preflight: read <code>references/cumcm-2026-latex.md</code>, start from <code>assets/latex/cumcm-2026/paper.tex</code>, build with <code>scripts/build_cumcm_latex.py</code>, and audit with <code>scripts/audit_cumcm_latex.py</code>. Recheck the current official notice before every formal submission.
- Time-limited work: read <code>references/competition-timeline.md</code>.
- Prompt design: read <code>references/ai-prompt-patterns.md</code>.
- Skill maintenance or generalization testing on historical problems: read <code>references/blind-benchmarking.md</code>, then use <code>scripts/blind_modeling_benchmark.py</code>. Keep judge rubrics outside the evaluated agent context until responses are frozen.

## Figure Workflow

Use quantitative figures for empirical evidence and code-native diagrams for mechanisms or workflows. During <code>explore</code>, create only diagnostics needed to understand model failure. During <code>delivery</code>, read the routed figure references, generate from traceable data, export editable vector plus final-size raster, run programmatic QA, and visually inspect the rendered output. For <code>word-only</code>, retain source data and code in the workspace but embed only necessary figures and tables in the DOCX.

## Result Lifecycle

Move successful results only through:

<code>exploratory → candidate → independently_validated → frozen → manuscript</code>

Use <code>rejected_infeasible</code>, <code>rejected_no_improvement</code>, or <code>rejected_fidelity_failure</code> as terminal states. A high score does not permit skipping feasibility, fidelity, structural validity, support adequacy, independent validation, or the instance-versus-policy boundary. Freeze only canonical results approved for writing, and promote to manuscript only after the document actually contains the verified result and its evidence boundary.

## Required Outputs by Request Type

- Triage: sub-question map, task family, objectives, constraints, data needs, 2-3 candidates, baseline, and major risk.
- Model plan: assumptions, mathematical formulation, candidate comparison, baseline, feasibility probe, metrics, validation design, and fallback.
- Code: input contract, executable source, deterministic command, outputs, error checks, and reproducibility record.
- Results: baseline comparison, semantic definitions, effective support or coverage, task-specific structural checks, uncertainty or robustness evidence, limitations, and a claim-evidence map.
- Figure: one-sentence visual message, justified chart/diagram archetype, non-redundant panel map, source-data links, uncertainty/statistics, generating code, SVG/PDF + PNG preview, grayscale check when relevant, QA JSON, and final-size visual QA.
- Paper: one-sentence argument, section and paragraph jobs, terminology ledger, evidence-backed results, consistent figures/tables, limitations, and no unsupported claims.
- Word-only: one final DOCX containing the necessary verified tables and figures; retain code, source data, and QA records in the working directory without requiring them as separate submission files.
- Paper-bundle: manuscript, executable code, canonical data/results, complete figure bundle, and audit records.
- CUMCM LaTeX: independently authored TeX source, compiled PDF, build manifest, format-audit JSON, supporting-material inventory, and completed page-by-page visual review.
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

<!-- skill-provenance:v1;owner=YANG985-CMD;id=YANG985-CMD-MMS-2026-v13;path=SKILL.md;sha256=5a4a932ce3357b7b1a0c4fe9ff2d1d5e7209f84b7be63713b85ddc4eb9fad81d;pub=0ofp8dKKJWMQK0LUC4dZDC8cynCRQlggy7cVeq7NfBo=;sig=Wpu715yHpT66SdT10ClnHxhkMcLzn0n3GrO3dow171t5-AVQecr3cQWyHZ2tadAZCu4DigRf7cnek11RPQYyAA== -->
