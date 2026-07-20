# Discrete-Event Scheduling

Use this route for machines, vehicles, queues, dispatching, production, ports, warehouses, and other systems whose state changes at events rather than fixed physical time steps.

## Formulation checklist

- State: resource occupancy, queues, positions, job attributes, clocks, and accumulated objective terms.
- Event calendar: event time, type, affected entities, deterministic tie-breaking rule.
- Actions: decisions available at the event, after applying the hard-constraint mask.
- Transition: exact order of completion, release, dispatch, movement, and score updates.
- Objective: define when each cost or reward is accrued and its unit.
- Terminal rule: horizon, completed jobs, empty system, or explicit cutoff treatment.

## Baselines

Start with a lawful deterministic dispatch rule such as FIFO, shortest processing time, earliest due date, nearest vehicle, or the current operating policy. A random policy is useful for debugging but is rarely the only defensible baseline.

## Search routes

- Small exact instances: enumeration, dynamic programming, MILP, or constraint programming for an optimality reference.
- Rolling decisions: MPC or Beam Search with an exact transition contract.
- Large static schedules: constructive heuristic plus local search, GA, SA, or tabu search with feasibility-preserving moves.
- Stochastic systems: scenario evaluation or simulation optimization with common random numbers.

Every route must use hard-constraint action masks. A penalty-only encoding is inadequate for mandatory service, safety, capacity, or precedence constraints.

## Validation

1. Hand-check a tiny trace and a tiny exact instance.
2. Check conservation and event-order invariants after every transition.
3. Compare surrogate and exact transitions for at least 50 steps and boundary cases.
4. Compare the proposed policy with lawful baselines under identical scenarios and seeds.
5. Report score, constraint violations, runtime, variability, and failure cases together.

If a policy appears to improve the objective by voluntary idling, skipping a mandatory action, changing event order, or using future information, treat that as a model defect until disproved.
