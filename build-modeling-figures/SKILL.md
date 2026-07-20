---
name: build-modeling-figures
description: Build and audit traceable quantitative plots and code-native modeling diagrams from existing modeling results. Use when the primary deliverable is a figure, diagram, figure bundle, or final-size visual QA rather than a complete modeling solution.
---

# Build Modeling Figures

Turn verified results into figures that make one defensible claim each. Keep quantitative evidence separate from illustrative diagrams and never use AI-generated imagery as empirical evidence.

## Figure workflow

1. Identify the claim, reader question, source result, variables, units, grouping, baseline, uncertainty, and final publication size.
2. Choose one route:
   - quantitative: comparison, distribution, forecast, residual, convergence, Pareto, sensitivity, robustness, spatial, network, or simulation trajectory;
   - diagram: problem structure, pipeline, layered system, feedback loop, contrast, taxonomy, or decision flow.
3. Complete `assets/templates/figure-contract-template.json` before generating a formal figure. Record source data, generating script, deterministic command, statistics, panel responsibilities, and review risks.
4. Use Python/Matplotlib for quantitative figures unless the authoritative result must remain in MATLAB. Export editable SVG/PDF and a 300 dpi PNG; add a grayscale preview when color carries categories.
5. Run `scripts/audit_figure_bundle.py` in strict mode, render at final size, inspect the actual PNG preview, and revise any overflow, unreadable label, missing unit, or unsupported caption.
6. For mechanisms or workflows, describe nodes and relationships in `assets/templates/modeling-diagram-spec-template.json` and run `scripts/build_modeling_diagram.py`.

## Quality rules

- Give every figure one primary conclusion and one clear caption.
- Tie every plotted value to a traceable result file, table, or verified source.
- Show baseline, uncertainty, units, validation boundaries, and constraint violations when they affect the claim.
- Do not hide failed cases, choose a chart for decoration, or let an attractive diagram stand in for quantitative evidence.
- If the source result is diagnostic-only or stale, label the figure accordingly and keep it out of paper-ready claims.

## Resources

- Workflow and chart selection: `references/modeling-figure-workflow.md`.
- Figure contracts and QA: `references/figure-contract-and-qa.md` and `references/figure-qa-checklist.md`.
- Reusable plotting backend: `assets/code/python/modeling_plotkit.py`.
- Demo bundle: `assets/code/python/demo_modeling_figure.py`.
- Diagram builder: `scripts/build_modeling_diagram.py`.
- Bundle auditor: `scripts/audit_figure_bundle.py`.
