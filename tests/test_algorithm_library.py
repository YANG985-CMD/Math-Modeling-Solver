from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "assets" / "code" / "python"))

from modeling_algorithms import (  # noqa: E402
    bootstrap_mean_ci,
    entropy_weights,
    gm11,
    genetic_algorithm,
    monte_carlo_estimate,
    rolling_origin_splits,
    solve_linear_program,
    topsis,
)


class AlgorithmLibraryTests(unittest.TestCase):
    def test_decision_algorithms_return_diagnostics(self) -> None:
        matrix = np.array([[10.0, 5.0], [8.0, 3.0], [12.0, 7.0]])
        weights = entropy_weights(matrix, benefit_mask=[True, False])
        result = topsis(
            matrix,
            weights["weights"],
            benefit_mask=[True, False],
        )
        self.assertAlmostEqual(float(weights["weights"].sum()), 1.0)
        self.assertEqual(result["ranking"].shape, (3,))
        self.assertIn("distance_best", result)

    def test_gm11_forecasts_positive_series(self) -> None:
        result = gm11([10, 12, 14, 17, 20], forecast_steps=2)
        self.assertEqual(result["forecast"].shape, (2,))
        self.assertTrue(np.all(result["forecast"] > 0))
        self.assertIn("posterior_error_ratio", result)

    def test_linear_program_uses_hard_constraints(self) -> None:
        result = solve_linear_program(
            [3.0, 2.0],
            sense="max",
            lhs_ineq=[[1.0, 1.0]],
            rhs_ineq=[4.0],
            bounds=[(0.0, None), (0.0, None)],
        )
        self.assertTrue(result["success"])
        self.assertAlmostEqual(float(result["objective_value"]), 12.0)
        self.assertTrue(result["constraint_feasible"])

    def test_monte_carlo_is_seeded_and_reports_uncertainty(self) -> None:
        sampler = lambda rng, n: rng.normal(size=n)
        first = monte_carlo_estimate(sampler, 500, seed=7)
        second = monte_carlo_estimate(sampler, 500, seed=7)
        self.assertEqual(first["estimate"], second["estimate"])
        self.assertEqual(first["confidence_interval"].tolist(), second["confidence_interval"].tolist())

    def test_genetic_algorithm_is_seeded(self) -> None:
        objective = lambda x: float(np.sum(x**2))
        first = genetic_algorithm(
            objective,
            [(-1.0, 1.0), (-1.0, 1.0)],
            population_size=12,
            generations=8,
            seed=11,
        )
        second = genetic_algorithm(
            objective,
            [(-1.0, 1.0), (-1.0, 1.0)],
            population_size=12,
            generations=8,
            seed=11,
        )
        np.testing.assert_allclose(first["best_solution"], second["best_solution"])

    def test_bootstrap_and_rolling_origin_are_reproducible(self) -> None:
        interval = bootstrap_mean_ci([1, 2, 3, 4], n_resamples=200, seed=4)
        self.assertEqual(interval["confidence_interval"].shape, (2,))
        splits = list(
            rolling_origin_splits(10, initial_train=4, horizon=2, gap=1, step=2)
        )
        self.assertEqual(len(splits), 2)
        for train, test in splits:
            self.assertLess(train[-1], test[0])


if __name__ == "__main__":
    unittest.main()
