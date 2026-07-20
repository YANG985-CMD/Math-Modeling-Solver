from __future__ import annotations

import numpy as np

from ._validation import as_matrix, benefit_flags


def entropy_weights(
    matrix: object,
    benefit_mask: object | None = None,
    *,
    epsilon: float = 1e-12,
) -> dict[str, np.ndarray]:
    """Return entropy weights and benefit-oriented normalized values.

    Constant criteria receive zero information weight.  A matrix whose every
    criterion is constant is rejected because the ranking is unidentified.
    """

    data = as_matrix(matrix)
    flags = benefit_flags(benefit_mask, data.shape[1])
    normalized = np.zeros_like(data)
    for column_index in range(data.shape[1]):
        column = data[:, column_index]
        low, high = float(column.min()), float(column.max())
        if np.isclose(high, low):
            continue
        if flags[column_index]:
            normalized[:, column_index] = (column - low) / (high - low)
        else:
            normalized[:, column_index] = (high - column) / (high - low)

    totals = normalized.sum(axis=0)
    informative = totals > epsilon
    if not informative.any():
        raise ValueError("all criteria are constant; entropy weights are undefined.")

    proportions = np.zeros_like(normalized)
    proportions[:, informative] = (
        normalized[:, informative] / totals[informative]
    )
    k = 1.0 / np.log(data.shape[0])
    entropy = -k * np.sum(proportions * np.log(proportions + epsilon), axis=0)
    divergence = np.maximum(0.0, 1.0 - entropy)
    weights = np.zeros(data.shape[1], dtype=float)
    weights_sum = divergence.sum()
    if weights_sum <= epsilon:
        weights[informative] = 1.0 / informative.sum()
    else:
        weights = divergence / weights_sum
    return {
        "weights": weights,
        "normalized_matrix": normalized,
        "entropy": entropy,
        "scores": normalized @ weights,
    }


def topsis(
    matrix: object,
    weights: object | None = None,
    benefit_mask: object | None = None,
) -> dict[str, np.ndarray]:
    """Rank alternatives with TOPSIS and return intermediate diagnostics."""

    data = as_matrix(matrix)
    flags = benefit_flags(benefit_mask, data.shape[1])
    norms = np.sqrt(np.sum(data**2, axis=0))
    if np.any(norms <= 1e-12):
        raise ValueError("TOPSIS cannot normalize an all-zero criterion.")
    if weights is None:
        weight_vector = np.full(data.shape[1], 1.0 / data.shape[1])
    else:
        weight_vector = np.asarray(weights, dtype=float).reshape(-1)
        if weight_vector.size != data.shape[1] or not np.isfinite(weight_vector).all():
            raise ValueError("weights must be finite and match the criteria count.")
        if np.any(weight_vector < 0) or weight_vector.sum() <= 0:
            raise ValueError("weights must be non-negative and have a positive sum.")
        weight_vector = weight_vector / weight_vector.sum()

    weighted = data / norms * weight_vector
    ideal_best = np.where(flags, weighted.max(axis=0), weighted.min(axis=0))
    ideal_worst = np.where(flags, weighted.min(axis=0), weighted.max(axis=0))
    distance_best = np.linalg.norm(weighted - ideal_best, axis=1)
    distance_worst = np.linalg.norm(weighted - ideal_worst, axis=1)
    denominator = distance_best + distance_worst
    scores = np.divide(
        distance_worst,
        denominator,
        out=np.full(data.shape[0], 0.5, dtype=float),
        where=denominator > 1e-12,
    )
    ranking = np.argsort(-scores, kind="stable")
    return {
        "scores": scores,
        "ranking": ranking,
        "weights": weight_vector,
        "ideal_best": ideal_best,
        "ideal_worst": ideal_worst,
        "distance_best": distance_best,
        "distance_worst": distance_worst,
    }
