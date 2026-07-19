# MATLAB-Native Workflow

Use this route when the user requests MATLAB, the authoritative simulator is MATLAB/Simulink, MATLAB toolboxes materially simplify the method, or moving the model across languages would create fidelity risk.

## Backend choice

Choose the backend from the user's requirement, existing code, solver availability, and validation burden:

- MATLAB: `linprog`, `intlinprog`, Optimization Toolbox, Global Optimization Toolbox, Statistics and Machine Learning Toolbox, Simulink, or existing `.m`/`.slx` models.
- Python: its native optimization, statistics, machine-learning, geospatial, and data ecosystem.
- Mixed: only when a documented file interface is simpler and less risky than reimplementation.

Do not reimplement an authoritative MATLAB simulator in Python solely to satisfy a plotting convention.

Write a backend contract before execution. Name the authoritative simulator, search controller, scoring implementation, exchanged variables, array shapes, indexing convention, tolerances, serialization format, and which backend owns the canonical result. If the user requires MATLAB-only execution, Python may not silently perform simulation, scoring, optimization, or result generation; use it only for explicitly approved orchestration or file inspection.

For a mixed MATLAB-Python workflow, pass the bridge preflight before consuming the formal search budget:

```text
python scripts/preflight_matlab_python_bridge.py --out audit/matlab-python-preflight.json
```

The preflight executes MATLAB and verifies scalar, array, JSON Unicode, and Chinese-path round trips. A Python-only mock is not a passing bridge test.

## MATLAB MCP execution

When a MATLAB MCP server is available:

1. Verify connection with a harmless version or workspace query.
2. Set the project directory explicitly and record it.
3. Run scripts/functions with fixed inputs and random seeds.
4. Capture console diagnostics, toolbox versions, commands, and generated artifacts.
5. Save canonical results as MAT and, when practical, a human-readable table format.
6. Reopen or reload saved outputs before treating them as reproducible evidence.

If MCP is unavailable, use a local non-interactive MATLAB command only when authorized and record the exact command. Never claim MATLAB execution from code inspection alone.

## MATLAB-native figures

MATLAB figures are acceptable final quantitative evidence when they satisfy the same contract as Python figures:

- generated from canonical arrays/tables by executable code;
- explicit units, baseline, uncertainty, sample/scenario count, and statistics;
- fixed physical size, readable final-size typography, and colorblind/grayscale redundancy;
- exported as editable PDF or SVG where supported, plus 300 dpi PNG;
- visually inspected after rendering.

Use `exportgraphics` for deterministic exports and save `.fig` only as an optional editable source, not the sole deliverable. A CSV/MAT handoff to Python is optional, not mandatory.

## Optimization-specific checks

- Apply hard-constraint masks before candidate evaluation.
- Save objective and violation histories together.
- Compare solver exit flags and feasibility, not just the objective number.
- For surrogate search or MPC, export step traces and pass the exact-transition fidelity gate.
- Preserve MATLAB indexing, event ordering, and numeric tolerances when any cross-language comparison is used.
- For path-dependent policies, save available actions, hard-mask survivors, the selected action, state hash, and cumulative score at every step. Compare baseline and intervention traces with `scripts/audit_decision_trace.py` before attributing a final-score change to one mechanism.
