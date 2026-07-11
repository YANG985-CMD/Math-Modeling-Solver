from __future__ import annotations

import numpy as np
from scipy.optimize import linprog


def _dea_input_efficiency(inputs: np.ndarray, outputs: np.ndarray) -> np.ndarray:
    """Compute simple input-oriented CCR DEA efficiencies."""
    x = np.asarray(inputs, dtype=float)
    y = np.asarray(outputs, dtype=float)
    n_units, n_inputs = x.shape
    n_outputs = y.shape[1]
    efficiencies = np.zeros(n_units, dtype=float)

    for idx in range(n_units):
        objective = np.concatenate([np.zeros(n_units), [1.0]])

        constraints = []
        rhs = []

        for row in range(n_inputs):
            coeff = np.concatenate([x[:, row], [-x[idx, row]]])
            constraints.append(coeff)
            rhs.append(0.0)

        for row in range(n_outputs):
            coeff = np.concatenate([-y[:, row], np.zeros(1)])
            constraints.append(coeff)
            rhs.append(-y[idx, row])

        bounds = [(0.0, None)] * n_units + [(0.0, 1.0)]
        result = linprog(
            c=objective,
            A_ub=np.asarray(constraints, dtype=float),
            b_ub=np.asarray(rhs, dtype=float),
            bounds=bounds,
            method="highs",
        )
        if not result.success:
            raise RuntimeError(f"DEA optimization failed for unit {idx}: {result.message}")
        efficiencies[idx] = result.x[-1]

    return efficiencies


def dea_topsis(
    inputs: np.ndarray,
    outputs: np.ndarray,
    extra_indicators: np.ndarray | None = None,
    weights: np.ndarray | None = None,
    benefit_mask: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Evaluate units with DEA first, then rank them with TOPSIS."""
    x = np.asarray(inputs, dtype=float)
    y = np.asarray(outputs, dtype=float)
    efficiency = _dea_input_efficiency(x, y)

    matrix_parts = [efficiency.reshape(-1, 1), y]
    if extra_indicators is not None:
        matrix_parts.append(np.asarray(extra_indicators, dtype=float))
    decision_matrix = np.column_stack(matrix_parts)

    n_criteria = decision_matrix.shape[1]
    if weights is None:
        weights = np.ones(n_criteria, dtype=float) / n_criteria
    else:
        weights = np.asarray(weights, dtype=float)
        weights = weights / weights.sum()

    if benefit_mask is None:
        benefit_mask = np.ones(n_criteria, dtype=bool)
    else:
        benefit_mask = np.asarray(benefit_mask, dtype=bool)

    norm = decision_matrix / np.clip(np.sqrt((decision_matrix**2).sum(axis=0)), 1e-12, None)
    weighted = norm * weights
    ideal_best = np.where(benefit_mask, weighted.max(axis=0), weighted.min(axis=0))
    ideal_worst = np.where(benefit_mask, weighted.min(axis=0), weighted.max(axis=0))
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))
    topsis_score = dist_worst / np.clip(dist_best + dist_worst, 1e-12, None)
    ranking = np.argsort(-topsis_score)

    return {
        "dea_efficiency": efficiency,
        "decision_matrix": decision_matrix,
        "topsis_score": topsis_score,
        "ranking": ranking,
        "ideal_best": ideal_best,
        "ideal_worst": ideal_worst,
    }
