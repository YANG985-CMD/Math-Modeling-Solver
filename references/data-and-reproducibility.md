# Data and Reproducibility

## Data Audit

For each input, record:

- source and retrieval date;
- file name, size, encoding, sheet or table names;
- row meaning, key fields, units, and time zone;
- missingness, duplicates, outliers, impossible values, and category drift;
- transformations and whether they are fitted on training data only;
- license, privacy, or redistribution limits when relevant.

Prefer a compact audit table with columns: field, type, unit, valid range, missing rate, action, and justification.

## Leakage Checklist

- Future information entering a forecast feature
- Target-derived features available only after the event
- Scaling, imputation, PCA, or feature selection fitted before the split
- Repeated entities appearing in both train and test
- Spatial neighbors split as if independent
- Hyperparameter tuning performed on the final test set
- Optimization calibrated using the scenario later called out-of-sample

Use chronological splits for temporal data, grouped splits for repeated entities, and spatial or blocked validation where nearby observations are dependent.

## Run-Mode Policy

### Formal

- Input provenance must be known.
- Synthetic values cannot replace missing real observations.
- Report only actually executed results.
- Keep raw inputs immutable and write derived data elsewhere.

### Demo

- Synthetic or toy inputs are allowed.
- Add a visible <code>illustrative_only</code> marker to manifests and outputs.
- Do not claim empirical validity for the real system.

### Blocked

- Preserve the formulation, code skeleton, and requested-data contract.
- State exactly which claims cannot be evaluated.

## Reproducibility Manifest

Record at minimum:

- run mode and timestamp;
- operating system and language version;
- dependency versions;
- random seeds and nondeterministic components;
- exact command;
- input paths and SHA-256 hashes where feasible;
- parameter configuration;
- source files and output files;
- whether the run completed successfully.

For stochastic methods, report distributions across seeds rather than only the best run.

## Reproduction Test

A result is reproducible when a clean run can:

1. locate the documented inputs;
2. install or identify dependencies;
3. execute the recorded command;
4. regenerate the stated artifacts;
5. match deterministic outputs exactly or stochastic outputs within declared tolerances.
