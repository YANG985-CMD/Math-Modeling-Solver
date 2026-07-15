# Blind Benchmarking

Use historical problem corpora to test transferable triage, model selection, and validation design without learning published answers.

## Integrity Protocol

Keep three phases separate:

1. **Prepare**: expose only the public suite, problem statements, declared references, attachments, the response template, and the skill under test. Do not expose a case rubric.
2. **Freeze**: validate every material hash and response field, require an explicit no-solution attestation, and freeze the response with a payload SHA-256.
3. **Score**: only after every independent run is frozen, load the judge-only rubric and calculate correctness and cross-run stability.

Run evaluated agents in fresh contexts. Do not pass intended answers, expected tags, prior outputs, suspected weaknesses, or another run's artifacts. A repository that contains a judge rubric is not an agent-facing evaluation bundle; exclude judge-only files from the evaluated context.

## Pilot Workflow

Download and verify the three-case public pilot without committing upstream materials:

```powershell
python scripts/blind_modeling_benchmark.py prepare `
  --suite benchmarks/blind-pilot-suite.json `
  --out-dir D:\blind-eval\materials
```

Give each independent run the public suite, `benchmarks/blind-response-template.json`, the prepared material directory, and this skill. Freeze each response before opening the rubric:

```powershell
python scripts/blind_modeling_benchmark.py freeze `
  --suite benchmarks/blind-pilot-suite.json `
  --response D:\blind-eval\responses\run-1.json `
  --out D:\blind-eval\frozen\run-1.json
```

After all runs are frozen, score them together:

```powershell
python scripts/blind_modeling_benchmark.py score `
  --rubric benchmarks/blind-pilot-rubric.json `
  --frozen D:\blind-eval\frozen\run-1.json D:\blind-eval\frozen\run-2.json `
  --out-dir D:\blind-eval\score
```

The scorer writes JSON, field-level CSV, and HTML.

## What the Scores Mean

- **Correctness** compares task-family routing, an acceptable transparent baseline, required validation safeguards, and data-risk recognition with an isolated rubric.
- **Stability** is the average pairwise Jaccard agreement across independent runs for task families, baselines, validation safeguards, and data risks.
- High stability can mean consistent error. High correctness on one small suite can mean overfitting. Report both, inspect per-subproblem components, and expand the holdout set before claiming generalization.

The bundled pilot is a regression and workflow test, not a competition leaderboard. Add new cases from legally usable sources, keep their judge rubrics isolated, and avoid tuning the skill only to the public pilot.

## Response Rules

- Use the canonical tag catalogs in the public suite so independent runs can be compared deterministically.
- State an objective, task families, baseline families, at least two candidate models, a provisional selection, validation safeguards, data risks, output contract, and assumptions for every declared subproblem.
- List only hashes of materials actually read.
- Do not report numerical results during triage.
- Treat attachment inspection as necessary evidence: titles alone do not reveal axes, sample size, missing-by-design fields, complex values, or scalability.

## Corpus Safety

Do not copy problem files, papers, or solution prose into this skill unless redistribution is explicitly permitted. Public suite files contain only external URLs, hashes, titles, original tags, and evaluation contracts. Keep downloaded upstream material outside the repository.
