# Validation Playbook

Validation must match the question. One generic accuracy score is not enough.

## Universal Sequence

1. Verify units, constraints, and limiting cases.
2. Compare with a transparent baseline.
3. Use an out-of-sample, holdout, scenario, or perturbation test.
4. Measure uncertainty or variability.
5. Inspect failure cases.
6. state the exact claim boundary.

## By Task Family

| Task | Minimum evidence | Stronger evidence | Common trap |
| --- | --- | --- | --- |
| Forecasting | rolling or chronological holdout; MAE/RMSE/MAPE as appropriate | residual diagnostics, interval coverage, regime tests | random split on time series |
| Classification | untouched test set; class-aware precision/recall/F1 | calibration, subgroup errors, repeated grouped CV | accuracy on imbalanced data |
| Ranking/evaluation | normalization and weight checks | rank correlation under perturbations, alternative weighting | reporting one fragile ranking |
| Optimization | feasibility and objective value | optimality gap or lower bound, multi-seed distribution, scenario stress | showing only the best heuristic run |
| Clustering | internal index plus interpretable profiles | stability under resampling and parameter changes | treating clusters as ground truth |
| Network/path | conservation and connectivity checks | edge/node perturbation, alternative-cost scenarios | infeasible or disconnected solution |
| ODE/dynamics | dimensional and initial-condition checks | parameter identifiability, residuals, scenario sensitivity | fitting without mechanism checks |
| Simulation | verification of rules and conservation | repeated replications, confidence intervals, scenario coverage | one random trajectory |
| Causal/statistical | diagnostics and uncertainty intervals | robustness to specifications and confounders | causal language from correlation |

## Robustness Design

Choose perturbations that reflect actual uncertainty:

- measurement noise and missingness;
- parameter ranges with domain meaning;
- alternative reasonable preprocessing;
- demand, price, capacity, or policy scenarios;
- random seeds and initialization;
- removal of influential samples or nodes.

Predefine the primary metric and acceptable degradation when possible.

## Evidence Summary

For every headline result, provide:

- baseline value;
- proposed-model value;
- absolute and relative change;
- uncertainty or variability;
- tested scenarios;
- known failure region;
- artifact path supporting the claim.

Do not call an improvement robust when it appears only for one seed, split, or hand-picked parameter setting.
