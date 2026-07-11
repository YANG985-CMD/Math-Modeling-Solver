from __future__ import annotations

from typing import Iterable, Sequence

import pulp


def solve_linear_program(
    objective: Sequence[float],
    lhs_ineq: Sequence[Sequence[float]] | None = None,
    rhs_ineq: Sequence[float] | None = None,
    lhs_eq: Sequence[Sequence[float]] | None = None,
    rhs_eq: Sequence[float] | None = None,
    bounds: Sequence[tuple[float | None, float | None]] | None = None,
    variable_names: Iterable[str] | None = None,
    sense: str = "max",
) -> dict[str, object]:
    """Solve a reusable linear program with PuLP."""
    n_vars = len(objective)
    names = list(variable_names or [f"x{i + 1}" for i in range(n_vars)])
    direction = pulp.LpMaximize if sense.lower() == "max" else pulp.LpMinimize
    problem = pulp.LpProblem("linear_program", direction)
    bounds = list(bounds or [(0, None)] * n_vars)

    variables = [
        pulp.LpVariable(names[i], lowBound=bounds[i][0], upBound=bounds[i][1])
        for i in range(n_vars)
    ]
    problem += pulp.lpSum(objective[i] * variables[i] for i in range(n_vars))

    if lhs_ineq and rhs_ineq:
        for row, limit in zip(lhs_ineq, rhs_ineq):
            problem += pulp.lpSum(row[i] * variables[i] for i in range(n_vars)) <= limit

    if lhs_eq and rhs_eq:
        for row, limit in zip(lhs_eq, rhs_eq):
            problem += pulp.lpSum(row[i] * variables[i] for i in range(n_vars)) == limit

    status_code = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    solution = {names[i]: pulp.value(variables[i]) for i in range(n_vars)}

    return {
        "status": pulp.LpStatus[status_code],
        "objective_value": pulp.value(problem.objective),
        "solution": solution,
    }
