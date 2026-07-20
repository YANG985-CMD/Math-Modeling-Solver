# Score-Gap Analysis

Use this gate before tuning an optimizer when the task has a scalar score, weighted sub-scores, a published comparison, or a known theoretical bound. Its job is to decide where improvement is mathematically valuable before choosing an algorithm.

## Required contract

For every additive score component record:

- name, direction (`max` or `min`), and weight;
- declared worst value and theoretical best value;
- executed baseline value;
- reference value when a paper, team, or official benchmark is available;
- the exact score formula when it is not a weighted normalized sum.

Do not force a non-additive competition score into the bundled analyzer. Derive its component contributions directly and document the correct marginal effect instead.

## Executable gate

Create a JSON contract:

```json
{
  "objective": "weighted service score",
  "components": [
    {
      "name": "throughput",
      "direction": "max",
      "weight": 0.6,
      "worst": 0,
      "theoretical_best": 100,
      "baseline": 62,
      "reference": 70
    }
  ]
}
```

Run:

```text
python scripts/analyze_score_gap.py score-contract.json --out-dir results/diagnostics/score-gap
```

The tool writes JSON and CSV with baseline score, theoretical headroom, reference gap, component ranks, and weighted gain per raw unit. Its normalization assumption is printed in the report; never hide that assumption.

## Decision rule

1. If the baseline is already close to the theoretical bound, investigate formulation or bound tightness before increasing search effort.
2. If the reference gap is concentrated in one component, improve the state, constraint, or decision logic that controls that component.
3. If a low-weight component has a large raw gap but little weighted headroom, do not prioritize it merely because its raw number looks large.
4. If the reference score cannot be reproduced under the same score contract, label the comparison non-equivalent.
5. Register any proposed change as a bounded experiment; do not start an open-ended hyperparameter sweep.

The analysis identifies valuable directions. It does not prove that the remaining headroom is attainable.
