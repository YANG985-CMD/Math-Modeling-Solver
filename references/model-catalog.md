# Evidence-Aware Model Catalog

Use this catalog after the problem contract is complete and before selecting a candidate model. It extends the task-family router with common baselines, upgrade mechanisms, validation evidence, and failure signals. It is a candidate catalog, not an automatic model authority.

## Selection contract

1. Classify the sub-question from its inputs, outputs, observation unit, dependency structure, objective, and constraints. Do not route from keywords alone.
2. Execute one transparent baseline before adding a candidate model. Record the baseline metric, feasibility, runtime, and known failure.
3. Select at most two candidate mechanisms that directly target an observed failure. A model name alone is not a modeling plan.
4. For every candidate, state assumptions, required data, objective/loss, constraints, primary metric, validation split, and failure signal.
5. Use the evidence gates already defined by this skill. A catalog entry cannot waive hard-constraint, exact-transition, candidate-validation, experiment-budget, or claim-boundary checks.

## Method record

Record these fields in the method decision for each candidate:

- `task_family`: the semantic task family, not merely a keyword match.
- `baseline`: the executed transparent reference method.
- `upgrade_trigger`: the observed baseline failure this mechanism addresses.
- `assumptions`: data, physical, statistical, and decision assumptions.
- `objective_and_constraints`: the mathematical target and legal action set.
- `validation`: split or replay protocol, structural checks, sensitivity, and robustness evidence.
- `failure_signal`: what would falsify or reject the candidate.
- `budget`: runtime, runs, candidate count, and stop rule.
- `implementation`: Python or MATLAB entry point and environment requirements.

The machine-readable counterpart is `model-routing-rules.json`. Read it only after the semantic classification; do not use its `signals` list as a substitute for problem analysis.

## Task-family additions

| Family | Transparent baseline | Upgrade only when evidence shows | Required validation focus |
| --- | --- | --- | --- |
| Forecasting and estimation | naive/seasonal-naive, linear trend, ARIMA | residual structure, nonlinear covariates, regime changes | temporal or grouped split, rolling backtest, residual diagnostics |
| Classification and detection | majority/class-frequency, logistic regression, decision tree | nonlinear boundary, class imbalance, calibration failure | group-aware split, F1/PR-AUC, confusion matrix, threshold sensitivity |
| Evaluation and ranking | equal-weight or stated weighted score | unstable ranks, disputed weights, efficiency structure | weight perturbation, rank stability, known-fact or expert comparison |
| Optimization, scheduling, routing | LP/MILP/DP, greedy or exact small-instance solver | nonlinearity, scale, uncertainty, or a named search plateau | feasibility, hard-constraint mask, exact replay, bound/reference gap |
| Clustering and profiling | standardized PCA plus K-means or hierarchical clustering | unstable clusters, non-spherical structure, noise | resampling stability, internal metrics, group interpretation |
| Mechanism and simulation | balance equation, difference/ODE model, conservation relation | parameter uncertainty, unmodeled residuals, stochastic scenarios | historical replay, units, invariants, extreme scenarios, sensitivity |
| Network, graph, and propagation | shortest path, flow, centrality, PageRank | network disruption, diffusion, multilayer or resilience objective | graph-construction audit, perturbation, connectivity/efficiency, propagation comparison |
| Uncertainty, risk, and robustness | bootstrap, scenario sweep, interval or Monte Carlo baseline | tail risk, worst-case collapse, chance constraints | declared perturbation/scenario set, quantiles, worst-case, uncertainty propagation |
| Spatial and inverse measurement | coordinate audit, interpolation, FFT/periodogram, simple regression | spatial dependence, latent-state tracking, ill-posed inversion | coordinate convention, support coverage, reconstruction invariants, held-out locations |

## Combination routes

Use a combination only when each component has a separate responsibility and the combined route has a falsifiable benefit.

- **Forecast → optimize**: propagate forecast error into downstream feasibility and utility; do not validate the predictor alone.
- **Evaluate → cluster**: separate ranking validity from cluster semantics and stability.
- **Mechanism + data correction**: preserve the mechanism as the authoritative state model; fit residuals only where residual structure is demonstrated.
- **Graph → optimize**: audit node, edge, and weight construction before optimizing on the graph.
- **Small-sample trend + state correction**: use a grey or trend baseline plus a state correction only when residual states are identifiable and stable.
- **Linear temporal structure + nonlinear residual**: use an ARIMA/state-space baseline and add a learned residual model only with enough temporal data and a fair rolling comparison.
- **Efficiency screen → discriminative ranking**: use DEA/TOPSIS only when inputs, outputs, comparability, and the tie-breaking purpose are explicit.

## Rejection rules

- Do not use LSTM/Transformer, GA/PSO, or a hybrid merely because it is listed as an “improvement”.
- Do not use K-fold validation for dependent temporal or grouped data unless the split preserves the dependency structure.
- Do not call one weighted solution a Pareto front; produce adequate non-dominated coverage or state the limitation.
- Do not treat a low loss, high silhouette score, or successful solver exit code as proof of structural or physical validity.
- Do not copy demo parameters from a template into a formal result without running the real data and recording provenance.
