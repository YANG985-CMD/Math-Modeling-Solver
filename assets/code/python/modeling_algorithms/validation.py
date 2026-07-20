from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from ._validation import as_vector


def bootstrap_mean_ci(
    values: object,
    *,
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int | None = None,
) -> dict[str, object]:
    """Return a percentile bootstrap interval for the sample mean."""

    data = as_vector(values, name="values")
    if n_resamples < 100:
        raise ValueError("n_resamples must be at least 100 for a useful interval.")
    if not 0 < confidence < 1:
        raise ValueError("confidence must lie strictly between zero and one.")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, data.size, size=(n_resamples, data.size))
    estimates = data[indices].mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    interval = np.quantile(estimates, [alpha, 1.0 - alpha])
    return {
        "estimate": float(data.mean()),
        "confidence_interval": np.asarray(interval, dtype=float),
        "confidence": confidence,
        "n_resamples": n_resamples,
        "seed": seed,
    }


def rolling_origin_splits(
    n_samples: int,
    *,
    initial_train: int,
    horizon: int = 1,
    step: int = 1,
    gap: int = 0,
    max_splits: int | None = None,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Yield leakage-aware expanding-window train/test index pairs."""

    if n_samples < 1 or initial_train < 1 or horizon < 1 or step < 1 or gap < 0:
        raise ValueError("sample and split sizes must be positive; gap cannot be negative.")
    produced = 0
    train_end = initial_train
    while train_end + gap + horizon <= n_samples:
        test_start = train_end + gap
        yield np.arange(train_end), np.arange(test_start, test_start + horizon)
        produced += 1
        if max_splits is not None and produced >= max_splits:
            return
        train_end += step
