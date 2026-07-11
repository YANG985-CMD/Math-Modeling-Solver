---
name: math-modeling-playbook
description: Use when the user wants help solving mathematical modeling competition problems, especially for problem triage, model selection, reusable algorithm templates, competition-paper structuring, or end-to-end modeling workflows.
---

# Math Modeling Playbook

Use this skill when the user is working on a mathematical modeling contest problem and needs either:

- rapid problem triage
- full solving workflow guidance
- Python or MATLAB template matching
- competition-style paper structuring

## Workflow

1. Determine which mode the user needs.
2. Read only the matching reference files.
3. Prefer reusable modeling logic over one-off answers.
4. When suggesting a model, explain fit, assumptions, and alternatives.
5. When suggesting code, point to the closest local asset template and explain what to change.
6. When the user gives a time limit, add the matching compressed mode from `references/competition-timeline.md`.

## Mode Routing

- Triage requests: read `references/problem-triage.md` and `references/model-selection.md`
- Model-fit requests: read `references/model-selection.md`
- Full workflow requests: read `references/standard-workflow.md`, `references/paper-writing.md`, and `assets/templates/problem-analysis-template.md`
- Code-template requests: read `references/algorithm-templates.md` and inspect `assets/code/python/` or `assets/code/matlab/`
- Paper-writing requests: read `references/paper-writing.md` and `assets/templates/paper-outline-template.md`
- Time-limited contest requests: read `references/competition-timeline.md`
- Prompting requests: read `references/ai-prompt-patterns.md`
- Advanced-method requests: read `references/advanced-model-combinations.md` and `references/when-to-upgrade-model-complexity.md`

## Output Expectations

- For problem-classification prompts, classify the task type, split the problem into sub-problems, identify objectives and constraints, and recommend 2-3 candidate model families plus a simplest defensible first-pass route.
- For full-workflow prompts, include assumptions, preprocessing, model plan, validation or sensitivity checks, and a paper structure.
- For code-template prompts, name the closest local Python or MATLAB asset, explain input format, parameters to edit, expected outputs, and validation checks.
- For advanced-method prompts, explain whether a single model is enough, whether an upgrade is justified, and which combination model best matches the failure of the baseline.
