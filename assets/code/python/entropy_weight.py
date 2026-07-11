from __future__ import annotations

import numpy as np


def entropy_weight(
    matrix: np.ndarray,
    benefit_mask: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Compute entropy weights and weighted scores."""
    data = np.asarray(matrix, dtype=float)
    m, n = data.shape
    benefit_mask = np.asarray(
        benefit_mask if benefit_mask is not None else np.ones(n, dtype=bool)
    )
    normalized = np.zeros_like(data, dtype=float)

    for j in range(n):
        column = data[:, j]
        c_min = column.min()
        c_max = column.max()
        if np.isclose(c_max, c_min):
            continue
        if benefit_mask[j]:
            normalized[:, j] = (column - c_min) / (c_max - c_min)
        else:
            normalized[:, j] = (c_max - column) / (c_max - c_min)

    proportions = normalized / np.clip(normalized.sum(axis=0, keepdims=True), 1e-12, None)
    k = 1.0 / np.log(m)
    entropy = -k * np.sum(proportions * np.log(proportions + 1e-12), axis=0)
    divergence = 1.0 - entropy
    weights = divergence / divergence.sum()
    scores = normalized @ weights

    return {
        "weights": weights,
        "scores": scores,
        "normalized_matrix": normalized,
    }
