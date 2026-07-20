from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy.optimize import linprog


def solve_linear_program(
    objective: Sequence[float],
    *,
    lhs_ineq: Sequence[Sequence[float]] | None = None,
    rhs_ineq: Sequence[float] | None = None,
    lhs_eq: Sequence[Sequence[float]] | None = None,
    rhs_eq: Sequence[float] | None = None,
    bounds: Sequence[tuple[float | None, float | None]] | None = None,
    sense: str = "min",
) -> dict[str, object]:
    """Solve an LP with SciPy and expose feasibility diagnostics.

    Constraints are passed directly to the solver; no penalty-only repair is
    performed.  ``sense='max'`` is converted to the minimization convention
    used by ``scipy.optimize.linprog``.
    """

    c = np.asarray(objective, dtype=float).reshape(-1)
    if c.size == 0 or not np.isfinite(c).all():
        raise ValueError("objective must contain finite values.")
    if sense.lower() not in {"min", "max"}:
        raise ValueError("sense must be 'min' or 'max'.")
    sign = -1.0 if sense.lower() == "max" else 1.0

    def matrix(value: Sequence[Sequence[float]] | None, name: str) -> np.ndarray | None:
        if value is None:
            return None
        result = np.asarray(value, dtype=float)
        if result.ndim != 2 or result.shape[1] != c.size:
            raise ValueError(f"{name} must have {c.size} columns.")
        if not np.isfinite(result).all():
            raise ValueError(f"{name} contains non-finite values.")
        return result

    def vector(value: Sequence[float] | None, name: str, rows: int | None) -> np.ndarray | None:
        if value is None:
            return None
        result = np.asarray(value, dtype=float).reshape(-1)
        if rows is not None and result.size != rows:
            raise ValueError(f"{name} length must match its constraint rows.")
        if not np.isfinite(result).all():
            raise ValueError(f"{name} contains non-finite values.")
        return result

    a_ub = matrix(lhs_ineq, "lhs_ineq")
    b_ub = vector(rhs_ineq, "rhs_ineq", None if a_ub is None else a_ub.shape[0])
    a_eq = matrix(lhs_eq, "lhs_eq")
    b_eq = vector(rhs_eq, "rhs_eq", None if a_eq is None else a_eq.shape[0])
    if (a_ub is None) != (b_ub is None) or (a_eq is None) != (b_eq is None):
        raise ValueError("each constraint matrix must be paired with its RHS vector.")
    variable_bounds = list(bounds or [(0.0, None)] * c.size)
    if len(variable_bounds) != c.size:
        raise ValueError("bounds length must match the number of variables.")

    result = linprog(
        sign * c,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=b_eq,
        bounds=variable_bounds,
        method="highs",
    )
    objective_value = None if result.fun is None else float(sign * result.fun)
    slacks = None if result.ineqlin is None else np.asarray(result.ineqlin.residual)
    return {
        "status": str(result.message),
        "success": bool(result.success),
        "objective_value": objective_value,
        "solution": None if result.x is None else np.asarray(result.x),
        "inequality_slack": slacks,
        "constraint_feasible": bool(result.success),
    }
