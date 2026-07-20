# Task-Family Router

Classify each sub-question independently, then map dependencies between outputs.

For the expanded baseline/upgrade/validation/risk catalog, read
`model-catalog.md` and `model-routing-rules.json` after this semantic triage.
Use the structured rules to check coverage, not to replace the problem
contract.

| Observable structure | Candidate baseline | Upgrade only if evidence demands it |
| --- | --- | --- |
| Multi-indicator ranking | equal-weight score, entropy-TOPSIS | AHP fusion, grey relation, DEA |
| Time-indexed prediction | naive or seasonal naive, linear trend, ARIMA | tree ensembles, state space, hybrid residual model |
| Tabular prediction/classification | mean/class-frequency, linear/logistic model | random forest, boosting, SVM, neural network |
| Resource allocation | LP or MILP | decomposition, robust/stochastic optimization, metaheuristic |
| Routing/scheduling | greedy rule or exact small-instance model | branch-and-bound strategy, GA/PSO/SA hybrid |
| Multi-objective decisions | explicit weighted baseline and trade-off table | Pareto optimization with justified selection rule |
| Unsupervised structure | PCA and k-means baseline | density, spectral, mixture, manifold methods |
| Network influence/path | shortest path, centrality, flow | dynamic, multilayer, or stochastic network model |
| Mechanism/evolution | balance equation, ODE, compartment model | PDE, delay, stochastic, or agent-based model |
| Queue/inventory/reliability | analytical queue or renewal baseline | discrete-event or Monte Carlo simulation |
| Statistical association | descriptive model and regression | hierarchical, Bayesian, survival, causal design |
| Spatial process | spatial summary and simple interpolation | kriging, spatial regression, spatial-temporal model |
| Spectral localization or inverse measurement | FFT/periodogram with declared coordinate convention | MUSIC, sparse recovery, atomic norm, calibrated inverse model |
| Repeated frames with moving latent state | framewise estimate plus nearest-neighbor association | Kalman/particle filtering, joint sparse tracking, online state estimation |
| Balanced reviewer/block assignment | balanced random assignment and overlap diagnostics | block design, bipartite optimization, multi-objective fairness model |

## Routing Questions

1. Is the goal explanation, prediction, ranking, optimization, simulation, or decision support?
2. What is the observation unit and dependency structure?
3. Which variables are controllable, observed, latent, or outcomes?
4. Are constraints hard, soft, stochastic, or multi-objective?
5. What would a transparent baseline look like?
6. What evidence can falsify the proposed method?
7. Which output becomes an input to another sub-question?
8. For complex arrays or signals, which axes represent time, sensors, frequency, frames, and targets?
9. Is missingness structural because only selected units enter a later stage?

## Dependency Map

Represent sub-questions as a directed acyclic graph when possible:

- node: sub-question, input contract, output contract, metric;
- edge: the exact artifact consumed downstream;
- fallback: if a cycle is unavoidable, define an iterative convergence criterion and maximum iteration count.

Run independent nodes in parallel only after their shared data contract is stable.
