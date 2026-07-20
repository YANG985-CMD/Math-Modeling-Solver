# Algorithm Templates

Use this schema:

- Algorithm
- Best-fit task types
- Input requirements
- Output structure
- Key parameters
- What to edit for a new problem
- Failure modes
- Paper explanation pattern
- Local asset path

## Initial Curated Template Set

For a single importable baseline, start with the unified API under
`assets/code/python/modeling_algorithms/`. It returns diagnostics and uses
explicit validation and seeds:

- `entropy_weights` and `topsis` for decision analysis;
- `gm11` for short positive series;
- `solve_linear_program` for hard-constrained LPs;
- `monte_carlo_estimate` and `bootstrap_mean_ci` for uncertainty;
- `rolling_origin_splits` for time-aware validation.

- Linear programming -> `assets/code/python/linear_programming.py`
- Integer programming -> `assets/code/python/integer_programming.py`
- TOPSIS -> `assets/code/python/topsis.py`
- Entropy weight -> `assets/code/python/entropy_weight.py`
- Grey prediction -> `assets/code/python/grey_prediction.py`
- ARIMA forecast -> `assets/code/python/arima_forecast.py`
- Genetic algorithm -> `assets/code/python/genetic_algorithm.py`
- Particle swarm -> `assets/code/python/particle_swarm.py`
- PCA + SVM -> `assets/code/python/pca_svm.py`

## Combination-Model Anchors

These are not all fully productized local hybrids yet, but they already have the closest anchor templates:

- AHP + Entropy Weight -> start from `assets/code/python/entropy_weight.py`
- AHP + Entropy Weight -> `assets/code/python/ahp_entropy_weight.py`
- TOPSIS + Grey Relation -> `assets/code/python/topsis_grey_relation.py`
- DEA + TOPSIS -> `assets/code/python/dea_topsis.py`
- GM(1,1) + Markov -> `assets/code/python/gm11_markov.py`
- ARIMA + LSTM -> start from `assets/code/python/arima_forecast.py`
- SVM + PSO -> `assets/code/python/svm_pso.py`
- GA + SA -> `assets/code/python/ga_sa.py`
- PSO + Tabu Search -> start from `assets/code/python/particle_swarm.py`
- MOPSO -> start from `assets/code/python/particle_swarm.py`
