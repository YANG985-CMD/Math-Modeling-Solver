from __future__ import annotations

from typing import Callable, Sequence

import numpy as np


def particle_swarm_optimization(
    objective: Callable[[np.ndarray], float],
    bounds: Sequence[tuple[float, float]],
    particles: int = 30,
    iterations: int = 100,
    inertia: float = 0.7,
    cognitive: float = 1.5,
    social: float = 1.5,
    maximize: bool = False,
    seed: int | None = None,
) -> dict[str, object]:
    """Run a reusable particle swarm optimizer."""
    rng = np.random.default_rng(seed)
    bounds_array = np.asarray(bounds, dtype=float)
    lower = bounds_array[:, 0]
    upper = bounds_array[:, 1]
    span = upper - lower
    dim = bounds_array.shape[0]

    positions = rng.uniform(lower, upper, size=(particles, dim))
    velocities = rng.uniform(-span, span, size=(particles, dim))

    def score(individual: np.ndarray) -> float:
        value = objective(individual)
        return value if maximize else -value

    personal_best_positions = positions.copy()
    personal_best_scores = np.array([score(p) for p in positions], dtype=float)
    global_best_idx = int(np.argmax(personal_best_scores))
    global_best_position = personal_best_positions[global_best_idx].copy()
    global_best_score = personal_best_scores[global_best_idx]
    history = [global_best_score]

    for _ in range(iterations):
        r1 = rng.random((particles, dim))
        r2 = rng.random((particles, dim))
        velocities = (
            inertia * velocities
            + cognitive * r1 * (personal_best_positions - positions)
            + social * r2 * (global_best_position - positions)
        )
        positions = np.clip(positions + velocities, lower, upper)

        scores = np.array([score(p) for p in positions], dtype=float)
        improved = scores > personal_best_scores
        personal_best_positions[improved] = positions[improved]
        personal_best_scores[improved] = scores[improved]

        global_best_idx = int(np.argmax(personal_best_scores))
        global_best_position = personal_best_positions[global_best_idx].copy()
        global_best_score = personal_best_scores[global_best_idx]
        history.append(global_best_score)

    return {
        "best_solution": global_best_position,
        "best_objective": objective(global_best_position),
        "history": np.asarray(history),
    }
