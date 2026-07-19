# Word OMML Delivery

Use this route for every Word modeling report that contains mathematics.

## Authoritative conversion route

1. Keep the manuscript source in Markdown or another Pandoc-readable text format. Write every formula as LaTeX math in that source.
2. Build the DOCX with Pandoc, optionally with the required competition `--reference-doc`. Pandoc must convert LaTeX math to native Word OMML.
3. Do not insert equations as plain text, stitched Unicode characters, or screenshots. If a formula changes, update the source and rebuild the DOCX instead of replacing the equation with `python-docx` text.
4. If Pandoc is unavailable or conversion fails, stop the Word build and report the blocker. Never downgrade formulas to plain text.

Example:

```powershell
pandoc paper\main.md --reference-doc paper\reference.docx -o paper\report.docx
```

## Mandatory delivery gate

Open the generated DOCX in Microsoft Word, render or export it to PDF, and inspect every page at final size. Check formulas, charts, captions, tables, page breaks, headers, references, and Chinese text for corruption.

Copy `assets/templates/word-visual-qa-template.json`, record the DOCX SHA-256, Word-rendered PDF, total pages, every reviewed page, reviewer, time, and the four required checks. Then run:

```powershell
python scripts/audit_word_delivery.py paper\report.docx `
  --qa-manifest audit\word-visual-qa.json `
  --root PROJECT_DIR `
  --out audit\word-delivery-audit.json
```

The audit must find at least one `m:oMath` object for a mathematical report and must confirm that every rendered page was reviewed. The JSON manifest records the review; it does not replace actually opening and inspecting the Word rendering.

## Frozen-number synchronization

Do not type headline numbers independently into the manuscript. Freeze them first, then generate the manuscript table from the canonical file:

```powershell
python scripts/render_frozen_results.py results\frozen-results.json `
  --root PROJECT_DIR `
  --out paper\generated\frozen-results.md `
  --manifest-out audit\frozen-results-render.json
```

Include the generated block in the authoritative manuscript source and rebuild the DOCX. If `frozen-results.json` changes, regenerate the block, rebuild Word, render again, and repeat the page review.
