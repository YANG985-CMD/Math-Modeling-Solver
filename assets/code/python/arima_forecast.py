from __future__ import annotations

import numpy as np
from statsmodels.tsa.arima.model import ARIMA


def arima_forecast(
    series: np.ndarray,
    order: tuple[int, int, int] = (1, 1, 1),
    forecast_steps: int = 1,
) -> dict[str, object]:
    """Fit an ARIMA model and forecast forward."""
    data = np.asarray(series, dtype=float).reshape(-1)
    model = ARIMA(data, order=order)
    fitted = model.fit()
    forecast = fitted.forecast(steps=forecast_steps)

    return {
        "model": fitted,
        "aic": fitted.aic,
        "bic": fitted.bic,
        "in_sample_fitted": fitted.fittedvalues,
        "forecast": np.asarray(forecast),
    }
