from __future__ import annotations

import numpy as np


def topsis_rank(
    matrix: np.ndarray,
    weights: np.ndarray | None = None,
    benefit_mask: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Rank alternatives with TOPSIS."""
    data = np.asarray(matrix, dtype=float)
    n_criteria = data.shape[1]
    weights = np.asarray(weights if weights is not None else np.ones(n_criteria), dtype=float)
    weights = weights / weights.sum()
    benefit_mask = np.asarray(
        benefit_mask if benefit_mask is not None else np.ones(n_criteria, dtype=bool)
    )

    norm = data / np.sqrt((data**2).sum(axis=0))
    weighted = norm * weights
    ideal_best = np.where(benefit_mask, weighted.max(axis=0), weighted.min(axis=0))
    ideal_worst = np.where(benefit_mask, weighted.min(axis=0), weighted.max(axis=0))

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))
    closeness = dist_worst / (dist_best + dist_worst)
    ranking = np.argsort(-closeness)

    return {
        "scores": closeness,
        "ranking": ranking,
        "ideal_best": ideal_best,
        "ideal_worst": ideal_worst,
    }
