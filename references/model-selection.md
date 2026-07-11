# Model Selection

Use this schema for every method:

- Problem fit
- When to use
- Assumptions
- Strengths
- Weaknesses
- Common pitfalls
- Companion methods
- Fallback alternatives

## Evaluation Methods

### TOPSIS
- Problem fit: multi-indicator ranking
- When to use: comparable alternatives with normalized indicators
- Assumptions: monotonic indicator preference can be defined
- Strengths: intuitive ranking
- Weaknesses: sensitive to normalization and weighting

### AHP
- Problem fit: expert-driven weighting
- When to use: clear hierarchy and pairwise judgment available

### Entropy Weight
- Problem fit: objective weighting from indicator dispersion
- When to use: data-driven weighting desired

### DEA
- Problem fit: efficiency comparison across decision-making units
- When to use: multiple inputs and outputs with efficiency focus

## Optimization Methods

### Linear Programming
- Problem fit: continuous optimization with linear objective and constraints

### Integer Programming
- Problem fit: discrete or yes-no decisions

### Genetic Algorithm
- Problem fit: nonlinear or hard combinatorial search

### Particle Swarm Optimization
- Problem fit: continuous black-box optimization

## Prediction Methods

### ARIMA
- Problem fit: short-term univariate time series forecasting

### Grey Prediction
- Problem fit: small-sample trend forecasting

### Random Forest / XGBoost
- Problem fit: nonlinear supervised prediction with tabular features

### LSTM
- Problem fit: sequence learning with enough data and time

## Combination Upgrade Signals

### When to stay with a single model
- The baseline already matches the task structure
- The result is stable enough for the contest goal
- Data or time are limited
- The extra model would be hard to validate

### When to consider a combination model
- Residuals still contain structure after a reasonable baseline
- Rankings are unstable under small weight changes
- Features are highly redundant or noisy
- A search algorithm is stagnating
- Multiple objectives should remain explicit

### First combination families to consider
- Evaluation: AHP + entropy weight, TOPSIS + grey relation, DEA + TOPSIS
- Prediction: GM(1,1) + Markov, ARIMA + LSTM, SVM + PSO
- Optimization: GA + SA, PSO + tabu search, MOPSO

For more detail, route to `references/advanced-model-combinations.md` and `references/when-to-upgrade-model-complexity.md`.
