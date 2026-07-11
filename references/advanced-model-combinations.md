# Advanced Model Combinations

Use this file when a basic single model is not enough and you need a defensible combination route.

For each combination, check:

- Primary task type
- Why the combination helps
- Entry conditions
- What each component is responsible for
- Validation focus
- Failure signals
- Paper explanation pattern
- Suggested local anchor template

## Evaluation Combinations

### AHP + Entropy Weight
- Primary task type: multi-indicator evaluation with both expert judgment and data variation
- Why the combination helps: AHP contributes structured subjective preference, while entropy weight adds objective dispersion-based correction
- Entry conditions: clear indicator hierarchy exists and at least moderate-quality indicator data are available
- What each component is responsible for: AHP sets prior weights, entropy weight adjusts for observed information content
- Validation focus: consistency ratio for AHP, weight sensitivity, ranking stability
- Failure signals: expert pairwise matrix is inconsistent, data quality is too weak, weight fusion becomes arbitrary
- Paper explanation pattern: use AHP to encode decision structure, use entropy weight to reduce purely subjective bias, then compare fused and unfused rankings
- Suggested local anchor template: `assets/code/python/entropy_weight.py`

### TOPSIS + Grey Relation
- Primary task type: ranking alternatives when closeness and trend similarity both matter
- Why the combination helps: TOPSIS emphasizes distance to ideal solutions, grey relation captures shape similarity across indicators
- Entry conditions: normalized indicator matrix, limited sample size, need for a more robust ranking than TOPSIS alone
- What each component is responsible for: TOPSIS gives ideal-solution closeness, grey relation adds relational similarity score
- Validation focus: whether rankings are stable under weighting changes and whether both sub-scores tell a coherent story
- Failure signals: the two rankings strongly disagree and no decision rule is stated, indicators are poorly normalized
- Paper explanation pattern: explain that one score reflects ideal proximity and the other reflects structural similarity, then fuse them with a stated rule
- Suggested local anchor template: `assets/code/python/topsis.py`

### DEA + TOPSIS
- Primary task type: efficiency evaluation followed by discriminative ranking
- Why the combination helps: DEA screens efficiency under multiple inputs and outputs, while TOPSIS breaks ties and ranks near-efficient units
- Entry conditions: multiple comparable decision-making units with input-output structure, many units may appear efficient under DEA alone
- What each component is responsible for: DEA estimates efficiency frontier, TOPSIS refines ranking among candidates
- Validation focus: sensitivity to input-output selection, frontier stability, whether TOPSIS indicators are derived consistently
- Failure signals: too few units for DEA, inputs and outputs are mixed conceptually, TOPSIS is added without a tie-breaking reason
- Paper explanation pattern: first evaluate efficiency, then use TOPSIS to improve discrimination among frontier or near-frontier units
- Suggested local anchor template: `assets/code/python/topsis.py`

### PCA + SVM
- Primary task type: high-dimensional classification or screening
- Why the combination helps: PCA reduces redundancy and noise, SVM performs classification on the compact feature space
- Entry conditions: many correlated features, limited labels, concern about overfitting or unstable boundaries
- What each component is responsible for: PCA extracts lower-dimensional representations, SVM performs the final classification
- Validation focus: retained variance, classification accuracy, precision/recall, robustness to component count
- Failure signals: too few samples relative to feature dimension, PCA removes discriminative structure, hyperparameters are not tuned at all
- Paper explanation pattern: use PCA to reduce multicollinearity and noise, then train SVM for classification in a lower-dimensional feature space
- Suggested local anchor template: `assets/code/python/pca_svm.py`

## Prediction Combinations

### GM(1,1) + Markov
- Primary task type: small-sample forecasting with residual state switching
- Why the combination helps: GM(1,1) captures the main trend, Markov correction handles regime-like residual variation
- Entry conditions: small sample, visible trend, residuals show state dependence rather than pure white noise
- What each component is responsible for: GM(1,1) produces the baseline trend, Markov chain corrects forecast states
- Validation focus: posterior error ratio, small error probability, residual state transition stability
- Failure signals: no interpretable state pattern in residuals, sample is too small even for state estimation, transition matrix is unstable
- Paper explanation pattern: use GM(1,1) for trend extraction and Markov adjustment for fluctuation correction around the trend
- Suggested local anchor template: `assets/code/python/grey_prediction.py`

### ARIMA + LSTM
- Primary task type: time-series forecasting with both linear dependence and nonlinear residual structure
- Why the combination helps: ARIMA models linear autocorrelation, LSTM captures nonlinear leftover patterns
- Entry conditions: enough sequential data, baseline ARIMA leaves structured residuals, forecasting accuracy matters enough to justify complexity
- What each component is responsible for: ARIMA models trend and autocorrelation, LSTM learns residual nonlinearities or parallel sequence features
- Validation focus: train/validation split discipline, residual diagnostics after ARIMA, improvement over single-model baselines
- Failure signals: short series, no residual structure after ARIMA, LSTM is used with tiny data and no regularization
- Paper explanation pattern: first separate the linear component with ARIMA, then model the nonlinear remainder using LSTM
- Suggested local anchor template: `assets/code/python/arima_forecast.py`

### SVM + PSO
- Primary task type: prediction or classification where SVM hyperparameters matter and search space is nontrivial
- Why the combination helps: PSO automates hyperparameter search instead of manual tuning
- Entry conditions: SVM baseline is promising but sensitive to `C`, kernel, or kernel-specific parameters
- What each component is responsible for: SVM handles prediction, PSO searches hyperparameters
- Validation focus: nested validation discipline, search bounds, repeatability across seeds
- Failure signals: optimization set leaks test information, PSO search space is arbitrary, tuned model does not outperform a simple baseline
- Paper explanation pattern: use PSO to optimize the SVM hyperparameters under a defined validation objective, then report the final predictive model
- Suggested local anchor template: `assets/code/python/particle_swarm.py`

## Optimization Combinations

### GA + SA
- Primary task type: hard combinatorial or nonlinear optimization where exploration and local refinement are both needed
- Why the combination helps: GA explores globally, SA improves local escaping and refinement
- Entry conditions: rugged objective surface, many local optima, pure GA converges too slowly or prematurely
- What each component is responsible for: GA generates diverse candidate solutions, SA performs local improvement on selected individuals
- Validation focus: convergence curves, repeatability across seeds, final objective distribution across runs
- Failure signals: algorithm is too slow for contest time, hybrid parameters are untuned, improvement over GA alone is negligible
- Paper explanation pattern: use GA for global search and SA for local refinement so the hybrid balances diversity and convergence quality
- Suggested local anchor template: `assets/code/python/genetic_algorithm.py`

### PSO + Tabu Search
- Primary task type: continuous or mixed optimization needing fast global movement plus short-term memory against cycling
- Why the combination helps: PSO moves the swarm efficiently, tabu search stabilizes local improvement and avoids revisiting weak neighborhoods
- Entry conditions: standard PSO oscillates or stagnates, neighborhood search can be defined clearly
- What each component is responsible for: PSO proposes promising regions, tabu search refines and avoids repeated poor moves
- Validation focus: convergence stability, tabu tenure sensitivity, runtime budget
- Failure signals: no neighborhood structure is defined, hybrid runtime overwhelms contest budget, gains are not reproducible
- Paper explanation pattern: combine PSO's global movement with tabu search memory to improve local exploitation and reduce cycling
- Suggested local anchor template: `assets/code/python/particle_swarm.py`

### MOPSO
- Primary task type: multi-objective optimization with competing goals
- Why the combination helps: extends PSO to approximate a Pareto front instead of a single optimum
- Entry conditions: at least two explicit objectives must be balanced and trade-offs matter to the decision
- What each component is responsible for: swarm search explores objective space, archive and dominance logic maintain Pareto candidates
- Validation focus: Pareto spread, dominance quality, selected compromise solution rationale
- Failure signals: objectives are actually reducible to one weighted score, archive rule is unclear, final choice from the Pareto set is unexplained
- Paper explanation pattern: formulate the problem as multi-objective, generate Pareto-efficient candidates, and select a compromise using a stated policy
- Suggested local anchor template: `assets/code/python/particle_swarm.py`

## How To Use This File

- Start with the simplest single-model baseline first.
- Upgrade only when the baseline leaves a clear gap that the combination is meant to fix.
- In the paper, explain the role split between components instead of listing methods without purpose.
- If contest time is short, prefer combinations that extend an existing template you already trust.
