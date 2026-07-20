---
name: deliver-cumcm-paper
description: Assemble, compile, and preflight evidence-backed CUMCM mathematical modeling papers and submission packages. Use when the primary request is LaTeX/PDF delivery, format compliance, frozen-result insertion, or final paper visual inspection.
---

# Deliver CUMCM Paper

Prepare a CUMCM paper from verified artifacts. This Skill owns document assembly and submission preflight; it does not invent model results, replace missing evidence, or decide whether an unvalidated method is scientifically correct.

## Delivery workflow

1. Lock the contest year, official notice, anonymity rules, page limit, active source-of-truth files, and delivery profile. Recheck the current official notice before formal submission.
2. Confirm that canonical values come from `results/frozen-results.json` or another explicitly approved source. Mark stale, diagnostic-only, or candidate values as blocked for manuscript use.
3. Build from the versioned template under `assets/latex/cumcm-2026/` and record the TeX source, compiler, input files, command, log, and output hash.
4. Use `scripts/render_frozen_results.py` when inserting canonical tables or manuscript numbers; do not retype authoritative values into the paper.
5. Compile with `scripts/build_cumcm_latex.py` and run `scripts/audit_cumcm_latex.py --strict` for margins, A4, abstract order, anonymity, references, cross-references, placeholders, support archive, and file-size checks.
6. Render the final PDF and inspect every page for equations, charts, tables, pagination, fonts, Chinese text, and overflow. Programmatic pass is not a substitute for visual inspection.
7. Return the PDF, TeX source, build manifest, audit JSON, supporting-material inventory, open risks, and page-review status.

## Paper rules

- Keep problem analysis, model, solve, validate, conclusion, and limitations consistent with the frozen evidence.
- Keep symbols, units, scenarios, numbers, figure captions, and table values synchronized across the manuscript and registries.
- Do not claim a prize, generalization, causality, Pareto front, or robustness beyond the recorded evidence.
- Preserve the source files and logs needed to reproduce the final PDF.
- Update the year-specific reference and template rather than silently reusing an old contest rule.

## Resources

- Argument and paper structure: `references/argument-first-paper-writing.md` and `references/paper-writing.md`.
- Current-year CUMCM checks: `references/cumcm-2026-latex.md` and `references/competition-timeline.md`.
- Template: `assets/latex/cumcm-2026/paper.tex`.
- Build: `scripts/build_cumcm_latex.py`.
- Frozen values: `scripts/render_frozen_results.py`.
- Strict audit: `scripts/audit_cumcm_latex.py`.
