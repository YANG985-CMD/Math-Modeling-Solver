# Data and Reproducibility

## Data Audit

For CSV, TSV, delimited TXT/DAT, Excel, or two-dimensional MAT data, start with the executable audit rather than filling the audit table from visual inspection alone:

```bash
python scripts/audit_dataset.py input.xlsx \
  --target label --time timestamp --group subject_id --split split \
  --out-dir audit/dataset
```

Install `pandas` and `numpy`; Excel may require `openpyxl` or `xlrd`, and MAT files require `scipy`. The command writes:

- `dataset-audit.json`: machine-readable findings, source hashes, role contract, and limitations;
- `dataset-audit-fields.csv`: one row per field for the project audit table;
- `dataset-audit.html`: a reviewable report for the team.

The auditor checks inferred field types, missingness, duplicate rows, constants, IQR outliers, extreme skew, mixed value units, class imbalance, exact or near-perfect target leakage, time ordering, temporal split overlap, group split leakage, and high-dimensional tables. Complex MAT fields are retained and summarized by magnitude; the model must still declare whether it uses real/imaginary parts or magnitude/phase. MATLAB structs and arrays above two dimensions require an explicit reshape contract.

Automated flags do not justify automatic deletion. An outlier may be the phenomenon of interest, and a strong target correlation may be a valid physical identity. Resolve each warning with provenance and domain reasoning.

For each input, record:

- source and retrieval date;
- file name, size, encoding, sheet or table names;
- row meaning, key fields, units, and time zone;
- missingness, duplicates, outliers, impossible values, and category drift;
- transformations and whether they are fitted on training data only;
- license, privacy, or redistribution limits when relevant.

Prefer a compact audit table with columns: field, type, unit, valid range, missing rate, action, and justification.

## External Problem Corpora

Historical contest repositories are useful as blind robustness benchmarks because their attachments contain heterogeneous encodings, legacy Excel files, matrices, complex values, irregular layouts, and incomplete metadata. Use them safely:

- check the repository and each artifact's license before copying or redistributing anything;
- when no license is declared, keep downloaded files temporary and commit only original code, synthetic test fixtures, source URLs, hashes, and derived interface lessons;
- audit the attachment before reading a published solution so the benchmark tests the workflow rather than answer recall;
- record which files and failure modes changed the implementation;
- never train claims or copy prose from winning papers without permission and source attribution.

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
