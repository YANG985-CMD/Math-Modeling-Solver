from __future__ import annotations

import numpy as np


def gm11_markov(
    series: np.ndarray,
    forecast_steps: int = 1,
    n_states: int = 3,
) -> dict[str, np.ndarray | float]:
    """Fit a GM(1,1) model and correct forecast states with a simple Markov chain."""
    x0 = np.asarray(series, dtype=float).reshape(-1)
    if x0.size < max(5, n_states + 2):
        raise ValueError("Need enough observations for GM(1,1) fitting and state estimation.")

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

    residual_ratio = np.divide(
        x0 - fitted,
        np.clip(fitted, 1e-12, None),
    )
    bins = np.quantile(residual_ratio, np.linspace(0, 1, n_states + 1))
    bins[0] = -np.inf
    bins[-1] = np.inf
    states = np.digitize(residual_ratio, bins[1:-1], right=True)

    transition = np.zeros((n_states, n_states), dtype=float)
    for left, right in zip(states[:-1], states[1:]):
        transition[left, right] += 1.0
    row_sums = transition.sum(axis=1, keepdims=True)
    transition = np.divide(transition, np.clip(row_sums, 1e-12, None))

    state_centers = np.array(
        [
            residual_ratio[states == s].mean() if np.any(states == s) else 0.0
            for s in range(n_states)
        ]
    )

    future_baseline = np.array(
        [cumulative(x0.size + i) - cumulative(x0.size + i - 1) for i in range(forecast_steps)]
    )
    current_state = int(states[-1])
    corrected = np.zeros(forecast_steps, dtype=float)
    future_states = np.zeros(forecast_steps, dtype=int)
    for idx in range(forecast_steps):
        next_state = int(np.argmax(transition[current_state])) if transition[current_state].sum() > 0 else current_state
        future_states[idx] = next_state
        corrected[idx] = future_baseline[idx] * (1.0 + state_centers[next_state])
        current_state = next_state

    return {
        "a": a,
        "b": b,
        "fitted": fitted,
        "baseline_forecast": future_baseline,
        "markov_corrected_forecast": corrected,
        "residual_ratio": residual_ratio,
        "states": states,
        "transition_matrix": transition,
        "future_states": future_states,
    }
