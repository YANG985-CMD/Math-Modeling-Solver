# Competition Timeline

Every mode keeps the five evidence gates. Shorter timelines reduce model scope, not truthfulness.

## 24-Hour Sprint

- 0-3h: Intake gate; problem contract, dependency map, and data audit
- 3-6h: Method gate; baseline, candidates, feasibility probe, route approval
- 6-14h: Computation gate; execute baseline and selected model
- 14-19h: Evidence gate; comparison, sensitivity, robustness, result freeze
- 19-24h: Manuscript gate; write, cross-check, audit, package

Allow one complexity upgrade only after the baseline is stable.

## 12-Hour Compressed Mode

- 0-2h: Intake and method selection
- 2-7h: one baseline and one selected model, both executable
- 7-9h: one high-value validation plus baseline comparison
- 9-12h: freeze results, write, audit

Prefer a template-friendly method and retain the baseline as fallback.

## 6-Hour Rescue Mode

- 0-1h: contract, data sanity check, and simplest defensible baseline
- 1-3.5h: execute and debug one method
- 3.5-4.5h: feasibility plus one sensitivity or holdout check
- 4.5-6h: freeze numbers, write a coherent minimal paper, audit

Do not add a combination model unless the simple route is invalid.

## Time-Pressure Cut Order

Cut in this order:

1. decorative plots;
2. low-value ablations;
3. secondary complex models;
4. optional extensions.

Do not cut input verification, baseline comparison, execution evidence, or claim consistency.
