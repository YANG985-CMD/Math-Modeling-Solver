from __future__ import annotations

import numpy as np


def topsis_grey_relation(
    matrix: np.ndarray,
    weights: np.ndarray | None = None,
    benefit_mask: np.ndarray | None = None,
    rho: float = 0.5,
    alpha: float = 0.5,
) -> dict[str, np.ndarray]:
    """Fuse TOPSIS closeness and grey relation for multi-criteria ranking."""
    data = np.asarray(matrix, dtype=float)
    n_criteria = data.shape[1]
    weights = np.asarray(weights if weights is not None else np.ones(n_criteria), dtype=float)
    weights = weights / weights.sum()
    benefit_mask = np.asarray(
        benefit_mask if benefit_mask is not None else np.ones(n_criteria, dtype=bool)
    )

    col_norm = np.sqrt((data**2).sum(axis=0))
    normalized = data / np.clip(col_norm, 1e-12, None)
    weighted = normalized * weights

    ideal_best = np.where(benefit_mask, weighted.max(axis=0), weighted.min(axis=0))
    ideal_worst = np.where(benefit_mask, weighted.min(axis=0), weighted.max(axis=0))

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))
    topsis_score = dist_worst / np.clip(dist_best + dist_worst, 1e-12, None)

    delta_best = np.abs(weighted - ideal_best)
    delta_min = delta_best.min()
    delta_max = delta_best.max()
    grey_coeff = (delta_min + rho * delta_max) / np.clip(delta_best + rho * delta_max, 1e-12, None)
    grey_score = (grey_coeff * weights).sum(axis=1)

    fused_score = alpha * topsis_score + (1.0 - alpha) * grey_score
    ranking = np.argsort(-fused_score)

    return {
        "topsis_score": topsis_score,
        "grey_score": grey_score,
        "fused_score": fused_score,
        "ranking": ranking,
        "ideal_best": ideal_best,
        "ideal_worst": ideal_worst,
    }
