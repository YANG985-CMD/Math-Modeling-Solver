from __future__ import annotations

import numpy as np


def gm11(series: np.ndarray, forecast_steps: int = 1) -> dict[str, np.ndarray | float]:
    """Fit a GM(1,1) grey prediction model."""
    x0 = np.asarray(series, dtype=float).reshape(-1)
    if x0.size < 4:
        raise ValueError("GM(1,1) usually needs at least four observations.")

    x1 = np.cumsum(x0)
    b_matrix = np.column_stack((-0.5 * (x1[:-1] + x1[1:]), np.ones(x0.size - 1)))
    y = x0[1:].reshape(-1, 1)
    a, b = np.linalg.lstsq(b_matrix, y, rcond=None)[0].reshape(-1)

    def cumulative(k: int) -> float:
        return (x0[0] - b / a) * np.exp(-a * k) + b / a

    fitted = np.empty_like(x0)
    fitted[0] = x0[0]
    for idx in range(1, x0.size):
        fitted[idx] = cumulative(idx) - cumulative(idx - 1)

    forecast = np.array(
        [cumulative(x0.size + i) - cumulative(x0.size + i - 1) for i in range(forecast_steps)]
    )
    residuals = x0 - fitted
    c_ratio = residuals.std(ddof=1) / x0.std(ddof=1)
    p_small_error = np.mean(np.abs(residuals - residuals.mean()) < 0.6745 * x0.std(ddof=1))

    return {
        "a": a,
        "b": b,
        "fitted": fitted,
        "forecast": forecast,
        "residuals": residuals,
        "posterior_error_ratio": c_ratio,
        "small_error_probability": p_small_error,
    }
