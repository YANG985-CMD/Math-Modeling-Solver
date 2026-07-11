# When To Upgrade Model Complexity

Use this file to decide whether to stay with a baseline model or move to a more complex combination model.

## Default Rule

Start with the simplest defensible single-model route. Upgrade only when you can name the failure of the baseline and the reason the added component addresses that exact failure.

## Good Reasons To Upgrade

### The baseline misses a known structure
- Example: ARIMA captures trend but residuals still show nonlinear dependence
- Upgrade logic: add a nonlinear residual learner such as LSTM

### The baseline ranking is too fragile
- Example: TOPSIS rank changes sharply with small weight changes
- Upgrade logic: add grey relation, entropy weight, or another stabilizing companion

### The feature space is too noisy or too high-dimensional
- Example: direct classification overfits with many correlated indicators
- Upgrade logic: use PCA before SVM or another classifier

### The optimizer gets trapped or converges poorly
- Example: GA or PSO repeatedly stalls in local optima
- Upgrade logic: add a local-search or memory mechanism such as SA or tabu search

### A single score hides real trade-offs
- Example: cost, risk, and benefit cannot be collapsed cleanly without losing decision meaning
- Upgrade logic: switch to a multi-objective method such as MOPSO

## Bad Reasons To Upgrade

- The complex model sounds more advanced
- You want the paper to look impressive without evidence
- The baseline has not been run carefully yet
- There is not enough data or time to support the added complexity
- You cannot explain what the second component contributes

## Evidence Checklist Before Upgrading

- The baseline result exists and has been checked
- The baseline failure is observable, not guessed
- The extra component has a precise job
- You still have enough contest time to validate the upgrade
- You can compare upgraded and baseline results fairly

## Fast Contest Heuristics

### 24-hour mode
- You can consider one meaningful upgrade after the baseline is stable
- Keep the baseline result as a fallback

### 12-hour mode
- Upgrade only if the weakness is obvious and the extension is template-friendly
- Prefer combinations close to your existing assets, such as PCA + SVM or TOPSIS + grey relation

### 6-hour mode
- Usually do not upgrade unless the baseline is clearly invalid
- Prefer a strong explanation of a simple model over a fragile complex pipeline

## Upgrade Paths By Task Type

### Evaluation
- Baseline: TOPSIS, entropy weight, AHP, DEA
- Upgrade triggers: unstable ranking, conflict between subjective and objective weights, many tied efficient units
- Typical upgrades: AHP + entropy weight, TOPSIS + grey relation, DEA + TOPSIS

### Prediction
- Baseline: ARIMA, GM(1,1), random forest, XGBoost
- Upgrade triggers: nonlinear residuals, regime switching, multiscale or hybrid behavior
- Typical upgrades: ARIMA + LSTM, GM(1,1) + Markov, SVM + PSO

### Optimization
- Baseline: linear programming, integer programming, GA, PSO
- Upgrade triggers: local optima, unstable convergence, explicit multi-objective trade-offs
- Typical upgrades: GA + SA, PSO + tabu search, MOPSO

## Paper Writing Rule

When you upgrade complexity, write one sentence for each of these:

- What the baseline could already do
- What it still failed to capture
- Why the added component is the smallest reasonable fix
- How the upgraded model was validated against the baseline
