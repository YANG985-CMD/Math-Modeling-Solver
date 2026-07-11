from __future__ import annotations

import numpy as np


_RI_TABLE = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


def _ahp_weights(pairwise_matrix: np.ndarray) -> dict[str, np.ndarray | float]:
    matrix = np.asarray(pairwise_matrix, dtype=float)
    eigenvalues, eigenvectors = np.linalg.eig(matrix)
    max_index = int(np.argmax(eigenvalues.real))
    lambda_max = float(eigenvalues[max_index].real)
    weights = np.abs(eigenvectors[:, max_index].real)
    weights = weights / weights.sum()

    n = matrix.shape[0]
    ci = 0.0 if n <= 2 else (lambda_max - n) / (n - 1)
    ri = _RI_TABLE.get(n, 1.49)
    cr = 0.0 if np.isclose(ri, 0.0) else ci / ri

    return {
        "weights": weights,
        "lambda_max": lambda_max,
        "ci": ci,
        "cr": cr,
    }


def _entropy_weights(matrix: np.ndarray, benefit_mask: np.ndarray) -> dict[str, np.ndarray]:
    data = np.asarray(matrix, dtype=float)
    m, n = data.shape
    normalized = np.zeros_like(data, dtype=float)

    for j in range(n):
        column = data[:, j]
        c_min = column.min()
        c_max = column.max()
        if np.isclose(c_min, c_max):
            continue
        if benefit_mask[j]:
            normalized[:, j] = (column - c_min) / (c_max - c_min)
        else:
            normalized[:, j] = (c_max - column) / (c_max - c_min)

    proportions = normalized / np.clip(normalized.sum(axis=0, keepdims=True), 1e-12, None)
    k = 1.0 / np.log(m)
    entropy = -k * np.sum(proportions * np.log(proportions + 1e-12), axis=0)
    divergence = 1.0 - entropy
    weights = divergence / np.clip(divergence.sum(), 1e-12, None)
    return {"weights": weights, "normalized_matrix": normalized}


def ahp_entropy_weight(
    matrix: np.ndarray,
    pairwise_matrix: np.ndarray,
    benefit_mask: np.ndarray | None = None,
    alpha: float = 0.5,
) -> dict[str, np.ndarray | float]:
    """Fuse AHP subjective weights and entropy objective weights."""
    data = np.asarray(matrix, dtype=float)
    n_criteria = data.shape[1]
    benefit_mask = np.asarray(
        benefit_mask if benefit_mask is not None else np.ones(n_criteria, dtype=bool)
    )

    ahp_result = _ahp_weights(pairwise_matrix)
    entropy_result = _entropy_weights(data, benefit_mask)
    fused_weights = alpha * ahp_result["weights"] + (1.0 - alpha) * entropy_result["weights"]
    fused_weights = fused_weights / fused_weights.sum()
    scores = entropy_result["normalized_matrix"] @ fused_weights
    ranking = np.argsort(-scores)

    return {
        "ahp_weights": ahp_result["weights"],
        "entropy_weights": entropy_result["weights"],
        "fused_weights": fused_weights,
        "scores": scores,
        "ranking": ranking,
        "consistency_ratio": ahp_result["cr"],
    }
