from __future__ import annotations

from typing import Callable, Sequence

import numpy as np


def _simulated_annealing_refine(
    objective: Callable[[np.ndarray], float],
    start: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    temperature: float = 1.0,
    cooling: float = 0.95,
    steps: int = 40,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = rng or np.random.default_rng()
    current = start.copy()
    current_value = objective(current)
    best = current.copy()
    best_value = current_value
    span = upper - lower

    for _ in range(steps):
        proposal = current + rng.normal(0.0, 0.1, size=current.shape) * span
        proposal = np.clip(proposal, lower, upper)
        proposal_value = objective(proposal)
        delta = proposal_value - current_value
        if delta < 0 or rng.random() < np.exp(-delta / max(temperature, 1e-12)):
            current = proposal
            current_value = proposal_value
            if current_value < best_value:
                best = current.copy()
                best_value = current_value
        temperature *= cooling

    return best


def ga_sa(
    objective: Callable[[np.ndarray], float],
    bounds: Sequence[tuple[float, float]],
    population_size: int = 50,
    generations: int = 100,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.1,
    elite_size: int = 4,
    sa_temperature: float = 1.0,
    sa_cooling: float = 0.95,
    sa_steps: int = 40,
    seed: int | None = None,
) -> dict[str, object]:
    """Run a simple GA with simulated annealing refinement on elites."""
    rng = np.random.default_rng(seed)
    bounds_array = np.asarray(bounds, dtype=float)
    lower = bounds_array[:, 0]
    upper = bounds_array[:, 1]
    dim = bounds_array.shape[0]

    population = rng.uniform(lower, upper, size=(population_size, dim))
    history: list[float] = []

    for _ in range(generations):
        fitness = np.array([objective(individual) for individual in population], dtype=float)
        elite_indices = np.argsort(fitness)[:elite_size]
        history.append(float(fitness[elite_indices[0]]))

        selection_weights = 1.0 / np.clip(fitness - fitness.min() + 1e-8, 1e-8, None)
        selection_weights = selection_weights / selection_weights.sum()
        selected = population[
            rng.choice(population_size, size=population_size, p=selection_weights)
        ].copy()

        for idx in range(0, population_size - 1, 2):
            if rng.random() < crossover_rate:
                alpha = rng.random(dim)
                left = alpha * selected[idx] + (1.0 - alpha) * selected[idx + 1]
                right = alpha * selected[idx + 1] + (1.0 - alpha) * selected[idx]
                selected[idx], selected[idx + 1] = left, right

        mutation_mask = rng.random(selected.shape) < mutation_rate
        noise = rng.normal(0.0, 0.1, size=selected.shape) * (upper - lower)
        selected = np.where(mutation_mask, selected + noise, selected)
        selected = np.clip(selected, lower, upper)

        elites = population[elite_indices]
        refined_elites = np.array(
            [
                _simulated_annealing_refine(
                    objective,
                    elite,
                    lower,
                    upper,
                    temperature=sa_temperature,
                    cooling=sa_cooling,
                    steps=sa_steps,
                    rng=rng,
                )
                for elite in elites
            ]
        )
        selected[:elite_size] = refined_elites
        population = selected

    final_fitness = np.array([objective(individual) for individual in population], dtype=float)
    best_idx = int(np.argmin(final_fitness))

    return {
        "best_solution": population[best_idx],
        "best_objective": float(final_fitness[best_idx]),
        "history": np.asarray(history),
    }
