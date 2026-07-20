from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.stats import norm


def monte_carlo_estimate(
    sampler: Callable[[np.random.Generator, int], object],
    n_samples: int,
    *,
    seed: int | None = None,
    confidence: float = 0.95,
) -> dict[str, object]:
    """Estimate a scalar expectation and return standard-error diagnostics.

    The sampler receives a seeded generator and the requested sample count.
    The confidence interval is a normal approximation; use replication or a
    task-specific uncertainty model when tails or dependence matter.
    """

    if n_samples < 2:
        raise ValueError("n_samples must be at least two.")
    if not 0 < confidence < 1:
        raise ValueError("confidence must lie strictly between zero and one.")
    values = np.asarray(sampler(np.random.default_rng(seed), n_samples), dtype=float).reshape(-1)
    if values.size != n_samples or not np.isfinite(values).all():
        raise ValueError("sampler must return exactly n_samples finite values.")
    mean = float(values.mean())
    standard_error = float(values.std(ddof=1) / np.sqrt(n_samples))
    z = float(norm.ppf(0.5 + confidence / 2.0))
    interval = np.array([mean - z * standard_error, mean + z * standard_error])
    return {
        "estimate": mean,
        "standard_error": standard_error,
        "confidence": confidence,
        "confidence_interval": interval,
        "n_samples": n_samples,
        "seed": seed,
    }
