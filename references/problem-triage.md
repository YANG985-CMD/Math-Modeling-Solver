# Problem Triage

## Fast Reading Checklist

- What are the final deliverables?
- Is the task prediction, evaluation, optimization, classification, clustering, simulation, or mechanism modeling?
- Are there explicit constraints?
- Is there a time dimension?
- Is there spatial, network, or path structure?
- Is there labeled data?
- Is there multi-objective trade-off?

## Decomposition Template

1. Restate the main problem in plain language.
2. Split it into sub-problems.
3. Separate known data from target outputs.
4. List objectives and constraints.
5. Match candidate model families.
6. Choose the simplest defensible first-pass route.

## Heuristic Mapping

- Forecast over time -> ARIMA, grey prediction, regression, random forest, XGBoost, LSTM
- Multi-indicator ranking -> entropy weight, TOPSIS, AHP, grey relation, fuzzy evaluation
- Resource allocation with constraints -> LP, ILP, 0-1 programming, dynamic programming
- Hard combinatorial search -> GA, PSO, SA, ACO
- Classification with labeled data -> SVM, decision tree, naive Bayes, neural network
- Structure discovery without labels -> PCA, clustering, SOM
- Mechanism and evolution systems -> differential-equation models, epidemic-style models, state-transition methods
