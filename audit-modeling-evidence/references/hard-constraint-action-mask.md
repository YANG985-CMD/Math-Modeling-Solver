# Hard-Constraint Action Mask

Hard constraints define the action space. They are not soft preferences and cannot be repaired only after search.

## Contract

At state `s` and time `t`, construct the feasible set before scoring actions:

```text
A_feasible(s, t) = {a in A : every hard constraint is satisfied}
```

Then require the optimizer, heuristic, policy, or MPC controller to choose only from `A_feasible`. A penalty may rank feasible actions, but it may not admit an infeasible action.

## Implementation pattern

1. Centralize hard constraints in one predicate or mask function shared by the exact simulator and candidate generator.
2. Generate the mask before expansion, mutation, sampling, or argmax.
3. Assert that the selected action belongs to the exact simulator's feasible-action set.
4. Record the reason each action is masked during diagnostic runs.
5. Define behavior for an empty feasible set as an explicit model branch; never default to an arbitrary action.

Examples include mandatory service, capacity, precedence, conservation, safety, time windows, mutually exclusive resources, and rules that forbid voluntary idling.

## Verification

Test each constraint with:

- one clearly feasible state;
- one single-constraint violation;
- simultaneous active constraints;
- boundary equality;
- an adversarial state where a high-scoring action is illegal.

Also compare surrogate and exact `feasible_actions` through the transition-fidelity gate. A solution with one hard-constraint violation is `rejected_infeasible`, regardless of objective value.
