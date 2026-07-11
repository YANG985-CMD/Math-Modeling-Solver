from __future__ import annotations

from typing import Callable, Sequence

import numpy as np


def genetic_algorithm(
    objective: Callable[[np.ndarray], float],
    bounds: Sequence[tuple[float, float]],
    population_size: int = 50,
    generations: int = 100,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.1,
    maximize: bool = False,
    seed: int | None = None,
) -> dict[str, object]:
    """Run a compact continuous genetic algorithm."""
    rng = np.random.default_rng(seed)
    bounds_array = np.asarray(bounds, dtype=float)
    lower = bounds_array[:, 0]
    upper = bounds_array[:, 1]
    dim = bounds_array.shape[0]

    population = rng.uniform(lower, upper, size=(population_size, dim))
    history: list[float] = []

    def score(individual: np.ndarray) -> float:
        value = objective(individual)
        return value if maximize else -value

    for _ in range(generations):
        raw_scores = np.array([score(individual) for individual in population], dtype=float)
        best_idx = int(np.argmax(raw_scores))
        history.append(float(raw_scores[best_idx]))

        shifted = raw_scores - raw_scores.min() + 1e-12
        probabilities = shifted / shifted.sum()
        selected = population[rng.choice(population_size, size=population_size, p=probabilities)].copy()

        for idx in range(0, population_size - 1, 2):
            if rng.random() < crossover_rate:
                alpha = rng.random(dim)
                left = alpha * selected[idx] + (1 - alpha) * selected[idx + 1]
                right = alpha * selected[idx + 1] + (1 - alpha) * selected[idx]
                selected[idx], selected[idx + 1] = left, right

        mutation_mask = rng.random(selected.shape) < mutation_rate
        mutation_values = rng.uniform(lower, upper, size=selected.shape)
        selected = np.where(mutation_mask, mutation_values, selected)
        selected = np.clip(selected, lower, upper)
        selected[0] = population[best_idx]
        population = selected

    final_raw_scores = np.array([score(individual) for individual in population], dtype=float)
    best_idx = int(np.argmax(final_raw_scores))
    best_solution = population[best_idx]
    best_objective = objective(best_solution)

    return {
        "best_solution": best_solution,
        "best_objective": best_objective,
        "history": np.asarray(history),
    }
