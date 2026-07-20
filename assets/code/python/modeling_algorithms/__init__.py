"""Small, validated building blocks for common modeling competition tasks.

The package deliberately returns plain dictionaries and NumPy arrays so that
results can be serialized into a project registry without hidden state.  It is
an executable starting point, not a replacement for task-specific validation.
"""

from .decision import entropy_weights, topsis
from .forecasting import gm11
from .optimization import solve_linear_program
from .simulation import monte_carlo_estimate
from .validation import bootstrap_mean_ci, rolling_origin_splits
from ga_sa import ga_sa
from genetic_algorithm import genetic_algorithm
from particle_swarm import particle_swarm_optimization

__all__ = [
    "bootstrap_mean_ci",
    "entropy_weights",
    "ga_sa",
    "genetic_algorithm",
    "gm11",
    "monte_carlo_estimate",
    "particle_swarm_optimization",
    "rolling_origin_splits",
    "solve_linear_program",
    "topsis",
]

__version__ = "0.1.0"
