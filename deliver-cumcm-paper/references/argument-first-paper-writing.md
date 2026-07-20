# Argument-First Paper Writing

Modeling papers should be drafted from verified evidence outward. Do not start by filling section headings with generic prose.

## Paper Contract

Before a full draft, record:

- paper type and target audience;
- decision or scientific problem;
- one-sentence argument;
- primary evidence;
- comparison baseline;
- applicability boundary;
- target format, language, and length;
- canonical terminology, notation, metrics, and units.

Use this argument pattern:

> For [problem and scope], we develop [approach] to achieve [decision or technical advance], supported by [main evidence] relative to [baseline], within [boundary].

If the claim, evidence, or boundary is ambiguous, confirm the contract before writing full prose. A scaffold with explicit placeholders is safer than invented substance.

## Reader Sequence

Organize the paper so a reader can answer:

1. Why does this problem matter?
2. What exactly is contributed?
3. Why should the formulation and evidence be trusted?
4. How can the result be reproduced or used for a decision?
5. Where does the conclusion stop working?

## Argument Chain for Modeling Work

Use:

<code>problem and scope → baseline gap → formulation → solution procedure → fair evaluation → sensitivity/robustness → decision insight → limitations</code>

Keep these distinct:

- what the model is;
- why each component is needed;
- how it is solved;
- how well it performs;
- why the result matters.

For every model component, write motivation, mechanism, and evidence. Remove components whose contribution cannot be explained or tested.

## Section Jobs

### Abstract

State the problem, gap, approach, strongest verified quantitative result, decision meaning, and boundary. Write it after results are frozen.

### Problem and Assumptions

Define deliverables, scope, variables, units, constraints, dependencies, and assumptions. State how consequential assumptions are checked.

### Model

Move from the baseline to the proposed formulation. Define symbols before use and connect each term or constraint to the real problem.

### Solution

Give enough algorithmic detail to reproduce the result: initialization, parameters, stopping rule, randomness, complexity, and implementation choices.

### Results

Lead with the question answered, then the evidence, comparison, uncertainty, and interpretation. A performance number must identify the dataset or scenario, metric, baseline, and conditions.

### Validation and Discussion

Explain feasibility, residuals, sensitivity, out-of-sample behavior, failure cases, computational cost, and the applicability boundary. Separate observed evidence from interpretation.

### Conclusion

Return to the decision or question, summarize only supported contributions, and state the most important limitation or next test.

## Paragraph Contract

Assign one job to each paragraph:

- context;
- gap;
- formulation;
- rationale;
- result;
- comparison;
- validation;
- implication;
- limitation.

The first sentence states that job. Later sentences provide evidence, reasoning, qualification, or transition. Split paragraphs that perform unrelated jobs.

## Terminology Ledger

Before drafting, lock one canonical form for every recurring:

- model, algorithm, module, dataset, and scenario;
- abbreviation;
- metric and statistical symbol;
- variable, subscript, unit, and constraint.

Do not vary technical terms for literary variety. If a canonical term changes, update the full manuscript and ledger together.

## Claim Calibration

- Use strong verbs only for direct, reproducible evidence.
- Use qualified language for indirect trends or plausible mechanisms.
- Delete unsupported claims such as universal superiority, complete robustness, or first-ever novelty.
- Distinguish statistical change, practical significance, and decision value.

## Revision Loop

Revise the smallest affected unit:

1. identify the claim or paragraph that is wrong;
2. determine whether the issue is evidence, framing, terminology, or flow;
3. edit only the affected paragraphs unless the argument structure must change;
4. rerun claim, terminology, figure, and frozen-number checks for the changed scope.

Do not rewrite the whole paper merely to fix one local disagreement.

## Manuscript Audit

Before delivery, verify:

- the one-sentence argument matches the abstract and conclusion;
- every major claim appears in the claim-evidence ledger;
- paper numbers match frozen results;
- figures and tables each have a unique argumentative role;
- terminology, notation, and units follow the ledger;
- comparisons are fair and reproducible;
- limitations reflect actual validation evidence;
- citations support the exact statements they follow.
