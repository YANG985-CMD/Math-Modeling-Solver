# Candidate Validation Contract

Use this contract when a candidate can look successful under one metric while still representing the wrong state, weak support, or a poor downstream decision. It applies especially to reconstruction, registration, clustering, anomaly detection, prediction-to-decision pipelines, and multi-objective optimization.

## 1. Freeze semantics before metrics

Record:

- coordinate axes, orientation, sign, units, and reference frame;
- exact metric formulas, discretization, normalization, and evaluation interval;
- whether a constraint is an equality, upper bound, budget, target, or preference;
- whether a quantity is directly observed, inferred, apparent, synthetic, or causal.

Do not rank two results until their metric definitions are aligned. A shared label does not imply a shared formula.

## 2. Report effective support and identifiability

For every headline parameter or state, report the evidence that actually identifies it:

- independent replicate, group, scenario, or fold count;
- contiguous spatial or temporal support, not only the number of isolated inliers;
- local coverage and missing-by-design regions;
- feature-to-sample ratio, topology completeness, and parameter confounding where relevant;
- low-support regions excluded from strong claims.

A robust or trimmed loss may accompany, but never replace, full-interval residuals, support length, coverage, and failure-region reporting.

## 3. Validate the reconstructed state

Choose invariants in the output domain. Examples include:

- geometry: continuity, single-valuedness where required, non-self-intersection, reference-axis consistency, and parameter stability across repeats;
- networks or hierarchies: connectivity, conservation, parent-child balance, known topology, and impossible-flow checks;
- registration: fused-state plausibility and coverage in addition to edge residual and cycle closure;
- clustering: resampling stability, subgroup profiles, and the boundary between statistical groups and semantic labels;
- anomaly detection: injected-event recovery, false alarms, delay, magnitude sensitivity, and localization;
- simulation or dynamics: conservation, limiting cases, event ordering, and exact-transition agreement.

Low residual, cycle consistency, silhouette score, or accuracy cannot substitute for these checks.

## 4. Keep four validation dimensions separate

- **Reproducibility** asks whether the same frozen inputs and code reproduce the same result in an independent rerun.
- **Sensitivity** varies modeling or policy parameters while holding the evaluation contract fixed.
- **Robustness** varies seeds, noise, disruptions, initial states, or scenarios that the claim is expected to tolerate.
- **Generalization** evaluates cases that did not guide model, schedule, guard-position, or hyperparameter selection.

Do not use a deterministic replay as sensitivity evidence, a parameter sweep as generalization evidence, or a same-instance score distribution as proof of a transferable policy. Record canonical input hashes for reproducibility. If sensitivity is genuinely inapplicable, state why. Every robustness report must name its perturbation families.

Declare the independence level as `same_run_replay`, `independent_rerun`, `held_out_cases`, or `external_blind_cases`. Promotion to independent validation requires at least `independent_rerun`; generalization claims require selection-free cases.

## 5. Declare instance-specific schedules

When the result contains hand-selected positions, a fixed action sequence, case-tuned guard intervals, or a schedule found on one supplied instance, mark `instance_specific_schedule.applicable` and provide the schedule artifact. Call it an instance solution unless held-out evidence validates a reusable policy. A high score on that same instance cannot justify policy generalization.

## 6. Separate stages and propagate uncertainty

For a multi-stage pipeline, validate each stage separately:

1. prediction, calibration, estimation, or reconstruction;
2. utility, cost, or loss definition;
3. feasibility and allocation or control logic;
4. final decision quality and sensitivity to upstream uncertainty.

Do not use classification accuracy as a proxy for portfolio value, anomaly score as proof of a physical event, or interpolation accuracy as proof of mechanism. Propagate probabilities, intervals, replicate variance, or scenario uncertainty into downstream decisions and report whether the decision changes.

## 7. Audit multi-objective coverage

Declare one of two claim types:

- `single_tradeoff_candidate`: one validated feasible point, with no Pareto-front claim;
- `pareto_front`: at least two non-dominated points with non-zero objective spans and an explained selection rule.

If a solver returns one survivor or exhausts its budget, label coverage as limited. Do not draw or describe a front from one point.

## 8. Promotion evidence

Start from `assets/templates/candidate-validation-template.json`, fill only observed evidence, and run:

```text
python scripts/audit_candidate_evidence.py audit/candidate-validation.json --root PROJECT_DIR
```

The report must pass the primary metric, feasibility, semantic, support, structural, reproducibility, sensitivity, robustness, independence, and claim-boundary checks. Generalization, instance-specific schedules, fidelity, multi-objective coverage, and pipeline checks are enforced according to the declared claim. Use the same report with `scripts/promote_validated_candidate.py`; a JSON file containing only `{"status":"passed"}` is not independent validation.

Promotion means the stated claim passed this contract within its declared boundary. It does not prove global optimality, causality, or generalization outside tested support.
