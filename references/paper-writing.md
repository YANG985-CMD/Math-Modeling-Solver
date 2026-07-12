# Competition Paper Writing

Read <code>argument-first-paper-writing.md</code> first for the paper contract, reader sequence, paragraph jobs, terminology ledger, and targeted revision loop. Use this file as the compact competition structure and consistency checklist.

## Standard Structure

1. Abstract
2. Problem restatement and deliverables
3. Assumptions and their checking conditions
4. Symbols, units, and data
5. Baseline and candidate-method rationale
6. Mathematical formulation and solution
7. Results, comparison, uncertainty, and robustness
8. Advantages, failure regions, and limitations
9. Conclusion

## Evidence-First Writing

- Write from frozen results, not memory or console screenshots.
- Lock the one-sentence argument and terminology ledger before drafting full sections.
- Give each headline quantitative claim an entry in the claim-evidence ledger.
- Explain what the baseline can do before claiming improvement.
- Separate observed results, interpretation, and speculation.
- State the population, time period, scenario, and metric for comparisons.
- Use verified citations only; never generate plausible-looking references.

## Consistency Checks

- Formula logic matches executed code.
- Every symbol is defined once and used consistently.
- Units agree across formulas, tables, figures, and prose.
- Figure axes, legends, captions, and uncertainty are readable.
- Abstract, body, and conclusion use the same canonical numbers.
- Every figure and table is referenced and interpreted.
- Limitations match the actual validation boundary.

## Common Rejection Risks

- unexplained weighting or tuning;
- test-set leakage;
- reporting only the best stochastic run;
- infeasible optimization outputs;
- sensitivity analysis unrelated to realistic uncertainty;
- complex models without baseline evidence;
- conclusions that exceed the data or scenarios tested.
