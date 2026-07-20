# CUMCM 2026 LaTeX Workflow

Use this workflow for 2026 National Undergraduate Mathematical Contest in Modeling paper formatting. Treat the official rules as the compliance authority and the bundled LaTeX file as a portable style implementation, not an official template.

## Official format contract

Verify the current notice before a formal submission. The 2026 revision published by the national organizing committee states:

- use white A4 paper with every margin at least 25 mm;
- place the title, abstract, and keywords on the abstract page and keep them within one page in principle;
- start centered Arabic page numbering from the abstract page at page 1;
- omit the table of contents;
- limit the main text to 30 pages; appendix pages are not limited;
- keep the abstract, main text, and appendix anonymous;
- cite every external source at the point of use and list it in the references;
- submit the electronic paper as one PDF generated from the LaTeX source, no larger than 20 MiB;
- omit the commitment and numbering pages from the electronic paper, so its first page is the abstract page;
- submit supporting material separately as one ZIP or RAR archive no larger than 20 MiB;
- list supporting-material files in the paper appendix and include complete runnable source code there.

This skill uses the LaTeX-to-PDF route for competition delivery even when the official notice permits another electronic-paper format.

Official sources:

- Format specification: <https://www.mcm.edu.cn/html_cn/node/4cd596519c9eb9fbd866398f6df0caa3.html>
- 2026 contest rules: <https://www.mcm.edu.cn/html_cn/node/9d8e511fe7a1447b35f53a82c908e2e0.html>

The official format does not prescribe a universal font family, font size, line spacing, or color. Keep those as style choices and never describe them as mandatory national rules.

## Bundled asset

Start from `assets/latex/cumcm-2026/paper.tex`. It is independently written with standard LaTeX packages and contains no copied community class file. Preserve these behaviors:

- `ctexart` with XeLaTeX and portable Fandol fonts;
- A4 paper and 25 mm margins;
- centered footer page number;
- no title page, identity field, commitment page, numbering page, or table of contents;
- abstract-first electronic-paper layout;
- three-line tables, numbered equations, figures, references, appendices, and code listings;
- explicit supporting-material file list in the appendix.

Replace every `\placeholder{...}` marker. Do not leave instructions, sample results, or placeholder figures in a formal paper.

## Argument-first section order

Adapt section names to the problem, while preserving the evidence chain:

1. problem restatement and deliverables;
2. problem analysis and data contract;
3. assumptions and checking conditions;
4. notation and units;
5. baseline, formulation, and solution procedure;
6. results, fair comparison, uncertainty, and robustness;
7. conclusions, limitations, and applicability boundary;
8. references;
9. appendix with supporting-material inventory and complete runnable code.

Avoid rigidly forcing every problem into the same number of model sections. Split by sub-question only when that improves the argument and dependency map.

## Build and audit

Build without relying on Perl or `latexmk`:

```text
python scripts/build_cumcm_latex.py paper.tex --output-dir build/cumcm
```

Run the format preflight after the PDF exists:

```text
python scripts/audit_cumcm_latex.py paper.tex \
  --pdf build/cumcm/paper.pdf \
  --support-archive support.zip \
  --body-pages 24 \
  --json-out build/cumcm/audit.json \
  --strict
```

Pass known identity strings with repeated `--forbidden-text` options. The audit checks source structure, margins, missing assets, duplicate or unresolved labels, placeholders, PDF size and page geometry, archive size, and optional identity strings. Automated checks do not prove anonymity or visual correctness.

## Final visual gate

Render the final PDF and inspect every page. Check:

- first page contains only the paper title, abstract, keywords, and page number;
- no contents page or identity information appears;
- equations, figures, tables, captions, and references are resolved and legible;
- floats do not create misleading separation or large unexplained gaps;
- the main-text page count is at most 30;
- appendix file names match the submitted support archive;
- the PDF and archive are each no larger than 20 MiB.

Freeze the accepted PDF hash and audit JSON with the manuscript evidence before submission.
