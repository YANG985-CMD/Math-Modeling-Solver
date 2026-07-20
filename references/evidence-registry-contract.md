# Evidence Registry Contract

The claim ledger is necessary but not sufficient for a competition-ready
project. Use the optional registry bundle when a result will be reused in a
paper, compared across runs, or reviewed by another person.

## Registries

| File | Purpose |
| --- | --- |
| `results/result-registry.csv` | One source-of-truth row per citable metric or result |
| `audit/poc-registry.csv` | Real-data proof-of-concept attempts and failures |
| `audit/run-record.csv` | Commands, inputs, parameters, seeds, versions, and exit status |
| `audit/figure-evidence.csv` | Claim, source data, generator, exports, and visual checks |
| `audit/numerical-diagnostics.csv` | Tolerances, stability, feasibility, and uncertainty checks |
| `audit/review-pass-items.csv` | Concrete reviewer observations, locations, and expected conditions |
| `audit/consistency-audit.csv` | Cross-file checks for numbers, units, scenarios, and terminology |

Run `scripts/init_evidence_bundle.py PROJECT_DIR` to create the headers. Run
`scripts/audit_evidence_bundle.py PROJECT_DIR` before freezing numbers or
delivering a paper.

## Freeze rules

- A `paper_ready` or `frozen` result must point to an existing artifact, run,
  validation status, and SHA-256 hash.
- A verified claim must point to a result, source artifact, or explicit
  diagnostic boundary; a free-form “passed” string is not evidence.
- A formal figure must record source data, generator, deterministic command,
  final-size visual QA, and human approval before it enters the manuscript.
- A review pass item must contain a file, locator, observed value, expected
  condition, and evidence path; “checked” alone is invalid.
- Freeze changes by supersession. Do not edit a cited number in place.

The registries organize evidence; they do not prove a model is correct. The
task-specific validation contract and human decision remain authoritative.
