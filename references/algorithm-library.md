# Algorithm Library Contract

`assets/code/python/modeling_algorithms/` is the unified, dependency-light
entry point for common competition baselines. It currently covers:

- decision analysis: entropy weights and TOPSIS;
- short-series forecasting: GM(1,1) with residual diagnostics;
- constrained optimization: linear programming through SciPy HiGHS;
- uncertainty: seeded Monte Carlo estimates and bootstrap intervals;
- structure-aware validation: rolling-origin splits.

The functions return plain dictionaries and arrays, expose intermediate
diagnostics, reject non-finite or ambiguous inputs, and accept explicit seeds.
They are starting points, not evidence of task validity. Every formal use must
record the input, command, parameters, output hash, baseline, and validation
boundary in the project registries.

Existing specialized templates under `assets/code/python/` remain available
for richer hybrids such as GM(1,1)+Markov, SVM+PSO, GA, PSO, and GA+SA. They
are experimental starting points until the task-specific constraints and
independent validation are recorded.
