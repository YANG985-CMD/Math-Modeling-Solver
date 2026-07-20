# Failure-to-Method Router

Use this reference after an executed baseline exposes a named failure. Select a mechanism that directly addresses the failure, then register a bounded comparison. Do not choose a method because it sounds advanced.

| Observed failure | Diagnose first | Candidate mechanism | Required falsification |
| --- | --- | --- | --- |
| Large gap to a known or theoretical bound | Score components and binding constraints | Reformulate the action space, decomposition, relaxation, or bound-guided search | Show which component gap closes under the same score contract |
| Feasible score plateaus early | Neighborhood coverage and duplicate candidates | Adaptive neighborhoods, variable-neighborhood search, restart, or population diversity | Compare equal candidate and runtime budgets |
| Good local choices produce a poor final schedule | First path divergence and delayed cost | Rolling horizon, MPC, Beam Search, look-ahead value, or terminal cost | Replay the exact simulator and attribute downstream score change after divergence |
| Penalty tuning oscillates between score and violations | Whether illegal actions remain searchable | Hard action mask, feasibility-preserving encoding, or constraint propagation | Zero hard violations before objective comparison |
| Surrogate search looks strong but exact replay degrades | Stepwise state, event order, tolerances, and indexing | Correct the transition contract, calibrate the surrogate, or reduce surrogate scope | Pass consecutive exact-transition fidelity checks before more search |
| Parameter choice is unstable | Response surface, interactions, and flat regions | Regularization, robust parameter region, ensemble policy, or simpler model | Report sensitivity ranges, not only the best point |
| Mean performance improves but worst cases collapse | Scenario composition and tail failures | Robust optimization, chance constraints, minimax regret, or scenario weighting | Report worst-case and lower-quantile behavior on declared scenarios |
| Cross-validation improves but deployment decision does not | Calibration, utility, and downstream constraints | Decision-focused loss, calibrated probabilities, stochastic programming, or revised utility | Compare downstream utility with propagated uncertainty |
| Training and validation are strong but new groups fail | Group leakage and domain shift | Group-aware validation, hierarchical model, domain adaptation, or invariant features | Use selection-free groups or external cases |
| Forecast residuals remain autocorrelated | Trend, seasonality, structural breaks, exogenous timing | State-space, ARIMA-family errors, dynamic regression, or change-point model | Residual diagnostics and rolling-origin evaluation improve |
| Nonlinear model gives little gain over baseline | Sample size, noise ceiling, and feature support | Feature correction, monotonic constraints, additive model, or retain baseline | Improvement exceeds a predeclared practical threshold |
| Clusters are unstable or semantically empty | Resampling stability and subgroup profiles | Feature redesign, consensus clustering, density model, or abandon semantic labels | Stable resampling plus interpretable group profiles |
| Reconstruction residual is low but geometry is impossible | Coverage, reference frame, continuity, and topology | Constrained fitting, topology-aware reconstruction, or joint registration | Output-domain invariants pass on the full interval |
| A single multi-objective point survives | Objective scaling, archive logic, and search coverage | Epsilon constraint, weighted sweeps, NSGA-family search, or reference directions | Produce multiple non-dominated points with non-zero objective spans |
| Solver runtime dominates the contest budget | Profiling, redundant evaluations, and separability | Vectorization, caching, warm starts, decomposition, parallel evaluation, or smaller search | Compare wall time and score at a fixed total budget |

## Selection rule

1. Name one observable baseline failure.
2. Select at most two mechanisms that target it through different assumptions.
3. State the expected signature of success before running.
4. Keep the score contract, data split, scenario set, and total search budget fixed.
5. Reject a mechanism that does not produce its expected signature, even if one seed is favorable.

Prefer data correction, formulation repair, and action-space repair before a larger optimizer. Escalate model complexity only when the remaining time supports independent validation.
