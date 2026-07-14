# Figure QA Checklist

Run this after rendering the final-size PNG preview and before exporting the final vector files.

## Programmatic checks

- no missing glyph or font warning;
- every quantitative axis has a variable label and unit when applicable;
- text is at or above the declared minimum size;
- titles, labels, legends, annotations, and panel marks stay inside the canvas;
- adjacent tick labels do not overlap;
- raster preview has the declared DPI and physical size;
- PDF avoids Type 3 fonts; SVG keeps editable text and avoids unexpected embedded JPEGs;
- contract, source script, source data, exports, and QA report all exist.

## Visual inspection

Inspect the preview at its intended printed size.

1. **Message** — Can a reader identify the main comparison, trend, or mechanism within seconds?
2. **Hierarchy** — Is the hero evidence dominant and supporting evidence quieter?
3. **Legibility** — Are labels, units, symbols, minus signs, Greek letters, and Chinese characters readable?
4. **Collision** — Do legends, annotations, error bars, labels, or colorbars cover data or each other?
5. **Panel alignment** — Are panel marks, plot edges, shared axes, and gaps aligned consistently?
6. **Color and grayscale** — Are categories distinguishable without relying on red versus green alone? Does the grayscale preview still work?
7. **Integrity** — Are uncertainty, sample counts, split boundaries, constraint violations, and excluded data represented honestly?
8. **Cross-panel consistency** — Does the same method/state use the same color, line, marker, unit, and scale across panels?

## Automatic rejection conditions

Revise before delivery if any is true:

- a quantitative claim comes from generated or illustrative imagery;
- an optimization figure omits known constraint violations;
- a forecast shows only fitted data while claiming generalization;
- a small-sample mean bar hides individual data;
- a categorical x axis is connected as if continuous;
- a truncated axis exaggerates a comparison without a visible break;
- `jet`, rainbow, 3D bars/pies, decorative gradients, or a dual y axis create misleading structure;
- the final figure requires shrinking in Word/LaTeX to fit.

Record each QA iteration as `issue → code change → new preview → status`. A successful export is not a pass until the preview has been inspected.
