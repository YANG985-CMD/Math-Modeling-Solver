# Modeling Figure Workflow

Treat a figure as a visual proof step. Select the plot from the claim, data structure, and validation need; select the style only after those are fixed.

## 1. Choose the evidence route

| Route | Use for | Required basis | Preferred output |
| --- | --- | --- | --- |
| Quantitative plot | measured, simulated, optimized, predicted, or benchmarked values | traceable data + executable code | SVG/PDF + PNG |
| Code-native diagram | problem structure, algorithm flow, architecture, feedback, decision logic | verified modules and relationships | editable SVG/PDF + PNG |
| Illustrative AI schematic | optional graphical abstract or concept draft | explicit user request + source-grounded prompt | labeled illustrative image |

Never use an AI-generated image to imitate observations, numerical results, uncertainty, maps, or model performance.

## 2. Write the figure brief before code

Complete these fields:

1. `core_message`: the one sentence the figure must establish;
2. `reader_question`: what a skeptical reader asks;
3. `paper_role`: setup, method, main result, comparison, validation, robustness, trade-off, or decision;
4. `archetype`: chart or diagram family;
5. `hero_evidence`: the panel/value carrying the conclusion;
6. `panels`: one unique job per panel;
7. `source_data`, `metric`, `baseline`, `sample_or_runs`, and `uncertainty`;
8. final width/height, backend, exports, and review risks.

Delete a panel if hiding it does not weaken the conclusion.

## 3. Quantitative chart selection for modeling

| Modeling question | Primary figure | Validation companion | Common misuse to block |
| --- | --- | --- | --- |
| Is the proposed method better? | dot/bar comparison with interval and baseline | per-scenario distribution or paired differences | bars without uncertainty or sample count |
| Does a forecast generalize? | observed vs forecast with interval and split marker | residual/time, residual distribution, coverage | one fit curve with no held-out boundary |
| Did optimization converge feasibly? | objective vs evaluation/iteration | constraint violation, best-so-far, runtime | objective alone while constraints fail |
| How sensitive is the answer? | ordered lines or heatmap | rank stability or feasible-region map | radar chart with incomparable scales |
| What is the trade-off? | Pareto scatter/front | chosen operating point and feasibility encoding | collapsing objectives with unexplained weights |
| Are groups different? | raw points + box/violin or paired plot | effect size and confidence interval | mean bars for small samples |
| Which factors matter? | coefficient/importance interval plot | permutation/stability results | importance bars without direction or uncertainty |
| Is classification reliable? | PR/ROC plus operating point | confusion matrix and calibration | accuracy-only comparison on imbalance |
| How does a state evolve? | trajectory with event bands | conservation/constraint residual | many equal-weight lines with no key state |
| Where is the solution? | map/network/path with context | distance, flow, capacity, or residual panel | decorative map without quantitative validation |
| Is a ranking stable? | ordered dot/lollipop chart | weight perturbation/rank distribution | radar-only ranking or pie chart |

Rules:

- Show individual observations when each group has fewer than 10 independent samples.
- Use line connections only for genuinely ordered or continuous x values.
- For proportions or probabilities, start at zero unless a clear break is declared.
- Avoid dual y axes; use aligned subplots sharing x instead.
- Use perceptually uniform sequential maps and centered diverging maps. Never use `jet` or rainbow maps.
- Split a figure when it has more than one primary conclusion, more than six legend items, or labels require severe rotation.

## 4. Diagram structure selection

| Argument type | Structure | Required visual logic |
| --- | --- | --- |
| Sequential algorithm | pipeline | inputs → transformations → outputs, with data types on important arrows |
| Multi-level model | layered system | group modules by responsibility and show interfaces |
| Control/RL/iterative process | closed loop | the feedback arrow must visibly close the cycle |
| Proposed vs baseline | contrast | preserve comparable notation; highlight only the actual difference |
| Hierarchical categories | taxonomy/tree | mutually clear parent-child relations |
| Branching rules | decision flow | decision diamonds, labeled branches, terminal outcomes |
| Mechanism inside a system | zoom-in composite | locate the module in context, then enlarge its internal steps |

Do not create architecture from an abstract alone. Obtain the method steps, modules, state variables, or verified program structure. Use a white background, flat vector shapes, short horizontal labels, restrained color families, and arrows that do not cross text.

## 5. Backend and reusable tools

### Python

Use `assets/code/python/modeling_plotkit.py` for:

- competition/Nature/IEEE/Chinese style presets;
- colorblind-safe semantic colors and redundant markers/line styles;
- final-size figures in millimetres;
- comparison, forecast, convergence, sensitivity heatmap, distribution, and Pareto helpers;
- aligned panel labels, previews, multi-format export, grayscale export, and in-memory layout QA.

Run `assets/code/python/demo_modeling_figure.py` to verify the environment and inspect a complete four-panel evidence figure.

### MATLAB result handoff

When the model is solved in MATLAB, save the canonical arrays, tables, units, and labels to CSV or MAT, record that export command in the contract, and render the paper figure with the Python toolkit. Do not manually copy values into plotting code.

### Code-native diagrams

Use `scripts/build_modeling_diagram.py --spec SPEC.json --out results/figures/figX` for pipeline, layered, closed-loop, or contrast layouts. The JSON spec must declare nodes, edges, labels, highlights, and the central message.

## 6. Size and style defaults

Use current target-venue guidance when the user names a venue. These are conservative starting points, not substitutes for the latest author instructions.

| Target | Single column | Double column | Typical minimum text | Panel labels |
| --- | ---: | ---: | ---: | --- |
| Modeling competition/report | 86 mm | 180 mm | 8 pt | (a), (b), ... |
| Nature-family | 89 mm | 183 mm | 5–7 pt | a, b, ... |
| IEEE | 89 mm | 182 mm | 7–8 pt | (a), (b), ... |
| Chinese journal | 80 mm | 170 mm | 8 pt | follow journal sample |

Use color for meaning, not decoration. Keep a method/scenario color stable across all panels. Reserve a strong accent for the proposed method, selected decision, violation, or inflection point. Add line style or marker redundancy and inspect a grayscale preview.

## 7. Statistical and modeling integrity

For each quantitative panel record:

- metric definition and unit;
- independent unit and sample/scenario count;
- split, fold, seed, or perturbation definition;
- center and spread/interval;
- baseline definition;
- statistical test and correction when used;
- source-data path and generating script.

A representative trajectory needs aggregate evidence unless the work is explicitly a case study. An optimizer's objective plot needs constraint feasibility. A forecast plot needs held-out or rolling-origin evidence. A ranking needs sensitivity to weights.

## 8. Export and QA loop

1. Draw directly at final dimensions.
2. Run the plotting library's in-memory QA.
3. Render a 150–200 dpi PNG preview.
4. Open and inspect the preview using the eight checks in `figure-qa-checklist.md`.
5. Fix the generating code, not the rendered bitmap.
6. Repeat up to three rounds; if it still fails, change the chart or split the figure.
7. Export an editable SVG and/or PDF master plus a 300 dpi PNG only after the preview passes.
8. Run `scripts/audit_figure_bundle.py` and save its JSON report.

## 9. Design influences

This workflow is an original synthesis informed by public, permissively licensed figure systems:

- `Yuan1z0825/nature-skills` (Apache-2.0): claim-first contracts, hero-panel hierarchy, export discipline;
- `Deepshare-Official/CCF-Figure` (MIT): research/diagram classification, structure-before-decoration, failure-mode checks;
- `Haojae/scipilot-figure-skill` (MIT): data-first chart selection, reusable style/export utilities, programmatic plus visual QA loop.

Do not copy their prose, example data, artwork, or source code into deliverables. Adapt the general methods to the current modeling evidence and keep all generated results traceable.
