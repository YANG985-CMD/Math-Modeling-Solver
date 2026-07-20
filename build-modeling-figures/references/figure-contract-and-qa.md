# Figure Contract and QA

A modeling figure is a visual proof step. Decide what it must establish before choosing a chart type, layout, or palette.

## Separate Evidence from Illustration

- Data figures must be generated from traceable input data and executable code.
- AI-generated images may support a conceptual overview, cover, or non-data schematic only.
- Never use generated imagery to simulate observations, experimental output, maps, model performance, or uncertainty.
- Label conceptual images as illustrative when a reader could mistake them for measured evidence.

## Figure Contract

Record these fields before plotting:

- figure ID and one-sentence message;
- role in the paper: setup, main result, comparison, mechanism, validation, robustness, trade-off, or decision;
- intended reader question;
- final medium and dimensions;
- computational backend and source script;
- panel map and unique evidence carried by each panel;
- hero evidence and supporting evidence;
- source-data paths;
- metric, sample size, uncertainty, and statistical definitions;
- accessibility and integrity risks;
- required SVG/PDF/PNG/TIFF outputs.

If hiding one panel does not weaken the conclusion, remove or merge it.

## Modeling Figure Archetypes

| Archetype | Best use | Typical hierarchy |
| --- | --- | --- |
| Decision overview | problem structure, variables, constraints, workflow | large system diagram plus compact outputs |
| Quantitative comparison | baseline versus proposed methods | hero metric plus secondary metrics |
| Forecast and residual | temporal fit and generalization | forecast panel plus residual and interval panels |
| Optimization landscape | convergence and solution trade-offs | objective/Pareto panel plus feasibility and stability |
| Ranking and sensitivity | final ranking and weight dependence | ranking panel plus perturbation/stability panel |
| Spatial/network solution | topology, flow, route, or regional pattern | main map/network plus quantitative validation |
| Mechanism and simulation | state evolution and scenario effects | model schematic plus trajectory and uncertainty |

Use one dominant panel when the evidence is not equally important. Equal-sized grids often hide the main result.

## Panel Logic

Build panels in an evidence sequence:

1. establish the system or decision context;
2. show the main result against a baseline;
3. explain the mechanism, structure, or localization when relevant;
4. validate with uncertainty, residuals, feasibility, or held-out data;
5. show sensitivity, robustness, failure cases, or trade-offs.

Do not show the same values as a pie, bar, and heatmap merely to fill space. Each panel must add a new variable, comparison, diagnostic, or decision implication.

## Visual Encoding Rules

- Keep a method or scenario color stable across all figures.
- Use neutral colors for context, one signal family for the main method, and one accent for exceptions.
- Do not rely on red versus green alone.
- Prefer direct labels when they reduce eye travel.
- Keep comparable axes and scales aligned.
- Show uncertainty visually when it affects interpretation.
- Avoid truncated axes that exaggerate differences; if a non-zero origin is justified, make it conspicuous.
- Use readable symbols and line styles in grayscale.

## Statistics and Traceability

For every quantitative panel, record:

- metric definition and unit;
- baseline definition;
- sample, fold, seed, or scenario count;
- center and spread or confidence interval;
- statistical test and correction when used;
- source-data path and generating script;
- data split or scenario definition.

Representative trajectories or cases must be paired with aggregate evidence unless the paper explicitly presents a case study.

## Export Contract

- Prefer SVG or PDF for charts and diagrams with editable text.
- Add a 300 dpi PNG preview; use higher resolution for dense raster or line-art requirements.
- Export at the intended final dimensions rather than shrinking an oversized canvas later.
- Verify fonts, labels, legends, lines, and panel markers at final size.
- Keep source data, plotting script, vector file, preview, and QA notes together.
- Open exported files and visually inspect them; a successful save call is not visual QA.

## Final QA

Confirm:

- the core visual message is visible in seconds;
- every panel has a distinct job;
- data, code, and frozen results agree;
- uncertainty and baseline comparisons are defined;
- labels, units, legends, and colors remain readable;
- no content is clipped or overlapping;
- vector text remains editable where required;
- captions explain the evidence without overstating it;
- conceptual/AI-generated elements are not confused with empirical data;
- each figure is referenced and interpreted in the manuscript.
