# Exact Simulation Contract

Use this contract when Beam Search, MPC, dynamic programming, reinforcement learning, a heuristic evaluator, or another search method uses a simplified state transition model.

## Single source of truth

Define one exact simulator as the authority for:

- time advancement and event ordering;
- state updates and resource conservation;
- action availability and hard constraints;
- objective accumulation and terminal conditions.

The search surrogate may be faster or vectorized, but it may not silently redefine any of these semantics.

## Step record

Export both surrogate and exact traces as JSON lists. Every step contains:

```json
{
  "step": 0,
  "time": 0.0,
  "state": {"queue": 2, "machine_busy": false},
  "action": "dispatch",
  "feasible_actions": ["dispatch", "hold"]
}
```

Use stable names, explicit units, deterministic seeds, and the same initial state and action sequence. For event-driven simulations, `time` is event time rather than loop count.

## Fidelity gate

Before expanding search width, horizon, population size, or training budget, compare at least 50 consecutive transitions:

```text
python scripts/check_transition_fidelity.py surrogate.json exact.json --min-steps 50 --out results/diagnostics/transition-fidelity.json
```

The gate fails on state, time, selected action, feasible-action set, trajectory-length, or exact-feasibility mismatches. Tolerances apply only to numeric comparisons and must be tighter than any decision threshold.

After the initial pass, repeat the check on boundary scenarios: empty/full queues, simultaneous events, resource exhaustion, ties, terminal steps, and every rare constraint branch.

## Failure handling

- Stop optimization and mark the candidate `rejected_fidelity_failure`.
- Reduce the mismatch to the first divergent transition.
- Fix the surrogate or remove it; do not calibrate objective weights to conceal the mismatch.
- Rerun all downstream results because a transition change invalidates search rankings and manuscript numbers.
