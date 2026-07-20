from __future__ import annotations

import numpy as np

from ._validation import as_vector


def gm11(series: object, forecast_steps: int = 1) -> dict[str, np.ndarray | float]:
    """Fit a GM(1,1) model with residual diagnostics.

    GM(1,1) is intended for positive, short, approximately exponential series.
    The returned diagnostics do not establish forecasting validity; use a
    time-aware holdout or rolling-origin check before making a forecast claim.
    """

    values = as_vector(series, name="series")
    if values.size < 4:
        raise ValueError("GM(1,1) requires at least four observations.")
    if forecast_steps < 1:
        raise ValueError("forecast_steps must be positive.")
    if np.any(values <= 0):
        raise ValueError("GM(1,1) requires strictly positive observations.")

    accumulated = np.cumsum(values)
    design = np.column_stack(
        (-0.5 * (accumulated[:-1] + accumulated[1:]), np.ones(values.size - 1))
    )
    a, b = np.linalg.lstsq(design, values[1:], rcond=None)[0]
    if abs(a) <= 1e-12:
        raise ValueError("GM(1,1) is numerically singular because a is near zero.")

    def accumulated_value(k: int) -> float:
        return float((values[0] - b / a) * np.exp(-a * k) + b / a)

    fitted = np.array(
        [accumulated_value(k) - accumulated_value(k - 1) for k in range(1, values.size)]
    )
    fitted = np.insert(fitted, 0, values[0])
    forecast = np.array(
        [
            accumulated_value(values.size + step)
            - accumulated_value(values.size + step - 1)
            for step in range(forecast_steps)
        ]
    )
    residuals = values - fitted
    scale = float(values.std(ddof=1))
    posterior_error_ratio = float(residuals.std(ddof=1) / scale) if scale else 0.0
    small_error_probability = float(
        np.mean(np.abs(residuals - residuals.mean()) < 0.6745 * scale)
    ) if scale else 1.0
    return {
        "a": float(a),
        "b": float(b),
        "fitted": fitted,
        "forecast": forecast,
        "residuals": residuals,
        "posterior_error_ratio": posterior_error_ratio,
        "small_error_probability": small_error_probability,
    }
