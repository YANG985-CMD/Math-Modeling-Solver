"""Generate a deterministic, evidence-oriented mathematical-modeling figure."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from modeling_plotkit import (
    add_panel_labels,
    export_figure,
    new_figure,
    plot_convergence,
    plot_forecast,
    plot_method_comparison,
    plot_sensitivity_heatmap,
    save_qa_report,
)


def _write_source_data(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_demo(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = out_dir / "data"
    figure_dir = out_dir / "figures"
    audit_dir = out_dir / "audit"

    rng = np.random.default_rng(20260714)
    methods = ["Baseline", "Regression", "Ensemble", "Ours"]
    scores = np.array([0.721, 0.781, 0.814, 0.862])
    errors = np.array([0.018, 0.015, 0.012, 0.009])

    time = np.arange(1, 41)
    signal = 2.2 + 0.035 * time + 0.35 * np.sin(time / 4.2)
    observed = signal + rng.normal(0, 0.075, len(time))
    predicted = signal + 0.025 * np.cos(time / 3.4)
    interval = 0.15 + 0.004 * np.maximum(time - 28, 0)

    iterations = np.arange(1, 51)
    objective = 8.0 + 8.5 * np.exp(-iterations / 10.5) + 0.08 * np.sin(iterations / 2)
    violation = np.maximum(0, 0.6 - iterations / 28)

    sensitivity = np.array(
        [
            [0.62, 0.68, 0.71, 0.70],
            [0.69, 0.77, 0.82, 0.80],
            [0.73, 0.83, 0.91, 0.88],
            [0.70, 0.79, 0.86, 0.84],
        ]
    )

    source_path = data_dir / "F1_demo_evidence.csv"
    rows = []
    for i in range(max(len(time), len(iterations))):
        rows.append(
            {
                "time": int(time[i]) if i < len(time) else "",
                "observed": f"{observed[i]:.6f}" if i < len(time) else "",
                "predicted": f"{predicted[i]:.6f}" if i < len(time) else "",
                "lower": f"{predicted[i] - interval[i]:.6f}" if i < len(time) else "",
                "upper": f"{predicted[i] + interval[i]:.6f}" if i < len(time) else "",
                "iteration": int(iterations[i]) if i < len(iterations) else "",
                "objective": f"{objective[i]:.6f}" if i < len(objective) else "",
                "violation": f"{violation[i]:.6f}" if i < len(violation) else "",
            }
        )
    _write_source_data(source_path, rows)

    fig, axes = new_figure(2, 2, target="competition", language="zh", column="double")
    plot_method_comparison(
        axes[0, 0],
        methods,
        scores,
        errors=errors,
        baseline=scores[0],
        highlight=3,
        ylabel="Validation score",
    )
    axes[0, 0].set_title("模型比较：提升超过不确定性")

    plot_forecast(
        axes[0, 1],
        time,
        observed,
        predicted,
        lower=predicted - interval,
        upper=predicted + interval,
        split_index=28,
        xlabel="时间 / d",
        ylabel="需求量 / a.u.",
    )
    axes[0, 1].set_title("预测与外推区间")

    plot_convergence(
        axes[1, 0],
        iterations,
        objective,
        violation=violation,
        baseline=9.0,
        xlabel="迭代次数",
        ylabel="目标函数值",
    )
    axes[1, 0].set_title("收敛过程与约束可行性")

    plot_sensitivity_heatmap(
        axes[1, 1],
        sensitivity,
        ["0.8", "0.9", "1.0", "1.1"],
        ["-10%", "-5%", "+5%", "+10%"],
        colorbar_label="Robustness score",
    )
    axes[1, 1].set_title("双因素敏感性")
    add_panel_labels(axes.ravel())

    figure_base = figure_dir / "F1_modeling_evidence"
    qa_path = audit_dir / "F1-figure-qa.json"
    qa_report = save_qa_report(fig, qa_path, min_text_pt=6.5)
    outputs = export_figure(fig, figure_base, grayscale=True, close=True)

    contract = {
        "schema_version": "2.1",
        "figures": [
            {
                "id": "F1",
                "core_message": "The selected model improves validation performance while retaining stable forecast, convergence, and sensitivity behavior.",
                "reader_question": "Does the selected model outperform the baseline and remain trustworthy under validation and perturbation?",
                "paper_role": "Main result and robustness evidence",
                "archetype": "four-panel quantitative evidence figure",
                "backend": "python-matplotlib",
                "source_script": str(Path(__file__).resolve()),
                "deterministic_command": "python demo_modeling_figure.py --out <OUTPUT_DIR>",
                "final_size_mm": {"width": 180, "height": 112},
                "hero_evidence": "Panel a: validation score with uncertainty and baseline",
                "panels": [
                    {"id": "a", "job": "compare", "metric_or_content": "validation score", "unique_evidence": "uncertainty and baseline"},
                    {"id": "b", "job": "validate", "metric_or_content": "forecast trajectory", "unique_evidence": "held-out interval"},
                    {"id": "c", "job": "diagnose", "metric_or_content": "objective", "unique_evidence": "constraint violations"},
                    {"id": "d", "job": "stress test", "metric_or_content": "robustness", "unique_evidence": "two-factor perturbation"},
                ],
                "source_data": [str(source_path.relative_to(out_dir))],
                "statistics": {
                    "metric": "validation score and forecast interval",
                    "unit": "dimensionless score; arbitrary demand unit",
                    "baseline": "baseline model score = 0.721",
                    "sample_or_runs": "deterministic demonstration; 40 observations",
                    "uncertainty": "method error bars and forecast interval shown",
                    "test_or_validation": "time split at observation 29",
                },
                "style": {
                    "target": "competition",
                    "language": "zh",
                    "color_semantics": {"blue": "model evidence", "vermillion": "selected or warning"},
                    "minimum_text_pt": 6.5,
                    "grayscale_required": True,
                },
                "exports": [str(path.relative_to(out_dir)) for path in outputs],
                "qa_report": str(qa_path.relative_to(out_dir)),
                "conceptual_or_ai_generated": False,
                "qa_status": qa_report["status"],
                "review_risks": ["Demonstration data must be replaced before paper use"],
            }
        ],
    }
    contract_path = out_dir / "figure-contract.json"
    contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"contract": contract_path, "outputs": outputs, "qa": qa_report}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("build/modeling-figure-demo"))
    args = parser.parse_args()
    result = build_demo(args.out.resolve())
    print(json.dumps({"contract": str(result["contract"]), "qa": result["qa"]}, ensure_ascii=False, indent=2))
    return 0 if result["qa"]["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
