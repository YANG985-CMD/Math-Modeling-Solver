"""Reusable plotting and export helpers for mathematical-modeling figures.

The module favors evidence-dense, final-size figures over decorative charts.  It
has no dependency on pandas or seaborn; NumPy, Matplotlib, and optional Pillow
are sufficient.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

MM_PER_INCH = 25.4

TARGETS = {
    "competition": {
        "single": (86, 64),
        "double": (180, 112),
        "font_pt": 8.5,
    },
    "nature": {"single": (89, 66), "double": (183, 112), "font_pt": 7.5},
    "ieee": {"single": (88, 66), "double": (181, 112), "font_pt": 8.0},
    "chinese": {"single": (82, 64), "double": (170, 112), "font_pt": 9.0},
}

# Color-blind-safe colors.  Meaning must also be carried by markers, hatches,
# line styles, direct labels, or ordering rather than by color alone.
PALETTE = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "yellow": "#F0E442",
    "black": "#222222",
    "gray": "#7A7A7A",
    "light_gray": "#D9D9D9",
}
MARKERS = ("o", "s", "^", "D", "P", "X", "v")
LINESTYLES = ("-", "--", "-.", ":")


def _installed_font(preferred: Sequence[str]) -> str:
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred:
        if name in installed:
            return name
    return "DejaVu Sans"


def figure_size_inches(
    target: str = "competition",
    column: str = "double",
    size_mm: Sequence[float] | None = None,
) -> tuple[float, float]:
    """Return exact final figure dimensions in inches."""
    if size_mm is None:
        if target not in TARGETS:
            raise ValueError(f"Unknown target: {target!r}")
        if column not in ("single", "double"):
            raise ValueError("column must be 'single' or 'double'")
        size_mm = TARGETS[target][column]
    if len(size_mm) != 2 or min(float(v) for v in size_mm) <= 0:
        raise ValueError("size_mm must contain two positive numbers")
    return tuple(float(v) / MM_PER_INCH for v in size_mm)


def setup_publication_style(
    target: str = "competition",
    language: str = "zh",
    column: str = "double",
    size_mm: Sequence[float] | None = None,
) -> dict:
    """Apply a publication-oriented Matplotlib style and return its settings."""
    if target not in TARGETS:
        raise ValueError(f"Unknown target: {target!r}")
    base = float(TARGETS[target]["font_pt"])
    latin = _installed_font(("Arial", "Helvetica", "DejaVu Sans"))
    cjk = _installed_font(
        ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC")
    )
    primary = cjk if language.lower().startswith("zh") else latin
    width, height = figure_size_inches(target, column, size_mm)
    mpl.rcParams.update(
        {
            "figure.figsize": (width, height),
            "font.family": "sans-serif",
            "font.sans-serif": [primary, latin, "DejaVu Sans"],
            "font.size": base,
            "axes.labelsize": base,
            "axes.titlesize": base + 0.5,
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.labelsize": base - 0.5,
            "ytick.labelsize": base - 0.5,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "legend.fontsize": base - 0.5,
            "legend.frameon": False,
            "lines.linewidth": 1.5,
            "lines.markersize": 4.5,
            "patch.linewidth": 0.7,
            "grid.linewidth": 0.45,
            "grid.alpha": 0.28,
            "grid.color": "#777777",
            "savefig.dpi": 300,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.unicode_minus": False,
        }
    )
    return {
        "target": target,
        "language": language,
        "column": column,
        "size_mm": [round(width * MM_PER_INCH, 3), round(height * MM_PER_INCH, 3)],
        "font": primary,
        "font_pt": base,
    }


def new_figure(
    nrows: int = 1,
    ncols: int = 1,
    *,
    target: str = "competition",
    language: str = "zh",
    column: str = "double",
    size_mm: Sequence[float] | None = None,
    squeeze: bool = True,
):
    """Create a final-size figure with constrained layout."""
    settings = setup_publication_style(target, language, column, size_mm)
    size = tuple(v / MM_PER_INCH for v in settings["size_mm"])
    return plt.subplots(
        nrows,
        ncols,
        figsize=size,
        constrained_layout=True,
        squeeze=squeeze,
    )


def plot_method_comparison(
    ax,
    labels: Sequence[str],
    values: Sequence[float],
    *,
    errors: Sequence[float] | None = None,
    baseline: float | None = None,
    highlight: int | None = None,
    ylabel: str = "Score",
):
    """Bar comparison with uncertainty and an optional baseline reference."""
    values = np.asarray(values, dtype=float)
    x = np.arange(len(values))
    colors = [PALETTE["blue"]] * len(values)
    hatches = [""] * len(values)
    if highlight is not None:
        colors[highlight] = PALETTE["vermillion"]
        hatches[highlight] = "///"
    bars = ax.bar(
        x,
        values,
        yerr=errors,
        capsize=2.5 if errors is not None else 0,
        color=colors,
        edgecolor=PALETTE["black"],
        linewidth=0.55,
        zorder=2,
    )
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)
    if baseline is not None:
        ax.axhline(
            baseline,
            color=PALETTE["gray"],
            linestyle="--",
            linewidth=1.0,
            label=f"Baseline = {baseline:g}",
            zorder=1,
        )
        ax.legend(loc="best")
    ax.set_xticks(x, labels)
    ax.set_xlabel("Method")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y")
    return bars


def plot_forecast(
    ax,
    x: Sequence[float],
    observed: Sequence[float],
    predicted: Sequence[float],
    *,
    lower: Sequence[float] | None = None,
    upper: Sequence[float] | None = None,
    split_index: int | None = None,
    xlabel: str = "Time",
    ylabel: str = "Value",
):
    """Plot observations, forecast, uncertainty, and train/test boundary."""
    x = np.asarray(x)
    observed = np.asarray(observed, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    ax.plot(
        x,
        observed,
        color=PALETTE["black"],
        marker="o",
        markevery=max(1, len(x) // 10),
        label="Observed",
    )
    ax.plot(x, predicted, color=PALETTE["blue"], linestyle="--", label="Predicted")
    if lower is not None and upper is not None:
        ax.fill_between(
            x,
            np.asarray(lower, dtype=float),
            np.asarray(upper, dtype=float),
            color=PALETTE["sky"],
            alpha=0.28,
            linewidth=0,
            label="Uncertainty interval",
        )
    if split_index is not None:
        ax.axvline(
            x[split_index],
            color=PALETTE["vermillion"],
            linestyle=":",
            linewidth=1.2,
            label="Validation start",
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y")
    ax.legend(loc="best", ncols=2)


def plot_convergence(
    ax,
    iterations: Sequence[float],
    objective: Sequence[float],
    *,
    violation: Sequence[float] | None = None,
    baseline: float | None = None,
    xlabel: str = "Iteration",
    ylabel: str = "Objective",
):
    """Plot optimization convergence without hiding infeasible iterations."""
    iterations = np.asarray(iterations)
    objective = np.asarray(objective, dtype=float)
    ax.plot(iterations, objective, color=PALETTE["blue"], label="Objective")
    if violation is not None:
        violation = np.asarray(violation, dtype=float)
        infeasible = violation > 0
        if np.any(infeasible):
            ax.scatter(
                iterations[infeasible],
                objective[infeasible],
                facecolors="none",
                edgecolors=PALETTE["vermillion"],
                marker="o",
                label="Constraint violated",
                zorder=3,
            )
    if baseline is not None:
        ax.axhline(baseline, color=PALETTE["gray"], linestyle="--", label="Baseline")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="both")
    ax.legend(loc="best")


def plot_sensitivity_heatmap(
    ax,
    matrix: Sequence[Sequence[float]],
    xlabels: Sequence[str],
    ylabels: Sequence[str],
    *,
    colorbar_label: str = "Response",
    cmap: str = "cividis",
    annotate: bool = True,
):
    """Render a sensitivity matrix with explicit factors and response scale."""
    matrix = np.asarray(matrix, dtype=float)
    image = ax.imshow(matrix, cmap=cmap, aspect="auto", interpolation="nearest")
    ax.set_xticks(np.arange(len(xlabels)), xlabels)
    ax.set_yticks(np.arange(len(ylabels)), ylabels)
    ax.set_xlabel("Factor B")
    ax.set_ylabel("Factor A")
    colorbar = ax.figure.colorbar(image, ax=ax, pad=0.02, fraction=0.05)
    colorbar.set_label(colorbar_label)
    if annotate and matrix.size <= 36:
        midpoint = (np.nanmin(matrix) + np.nanmax(matrix)) / 2
        for row in range(matrix.shape[0]):
            for col in range(matrix.shape[1]):
                color = "white" if matrix[row, col] < midpoint else PALETTE["black"]
                ax.text(col, row, f"{matrix[row, col]:.2f}", ha="center", va="center", color=color)
    return image


def plot_group_distribution(
    ax,
    labels: Sequence[str],
    groups: Sequence[Sequence[float]],
    *,
    ylabel: str = "Value",
):
    """Show raw observations together with robust distribution summaries."""
    clean = [np.asarray(group, dtype=float) for group in groups]
    positions = np.arange(1, len(clean) + 1)
    box = ax.boxplot(clean, positions=positions, widths=0.5, patch_artist=True, showfliers=False)
    for patch in box["boxes"]:
        patch.set(facecolor=PALETTE["sky"], alpha=0.35, edgecolor=PALETTE["blue"])
    for idx, group in enumerate(clean, start=1):
        jitter = np.linspace(-0.16, 0.16, len(group)) if len(group) > 1 else np.zeros(1)
        ax.scatter(
            idx + jitter,
            group,
            s=13,
            facecolor=PALETTE["orange"],
            edgecolor="white",
            linewidth=0.35,
            alpha=0.8,
            zorder=3,
        )
    ax.set_xticks(positions, labels)
    ax.set_xlabel("Group")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y")
    return box


def plot_pareto(
    ax,
    x: Sequence[float],
    y: Sequence[float],
    *,
    feasible: Sequence[bool] | None = None,
    selected: int | None = None,
    xlabel: str = "Objective 1",
    ylabel: str = "Objective 2",
):
    """Plot a two-objective trade-off while preserving feasibility evidence."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    feasible_arr = np.ones(len(x), dtype=bool) if feasible is None else np.asarray(feasible, dtype=bool)
    ax.scatter(x[feasible_arr], y[feasible_arr], color=PALETTE["blue"], marker="o", label="Feasible")
    if np.any(~feasible_arr):
        ax.scatter(
            x[~feasible_arr],
            y[~feasible_arr],
            facecolors="none",
            edgecolors=PALETTE["gray"],
            marker="x",
            label="Infeasible",
        )
    if selected is not None:
        ax.scatter(
            [x[selected]],
            [y[selected]],
            s=75,
            marker="*",
            color=PALETTE["vermillion"],
            edgecolor=PALETTE["black"],
            linewidth=0.5,
            label="Selected solution",
            zorder=4,
        )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid()
    ax.legend(loc="best")


def add_panel_labels(axes: Iterable, labels: Sequence[str] | None = None) -> None:
    """Add stable panel labels in axes coordinates."""
    axes = list(np.asarray(list(axes), dtype=object).ravel())
    labels = labels or [chr(ord("a") + i) for i in range(len(axes))]
    for ax, label in zip(axes, labels):
        ax.text(
            -0.12,
            1.04,
            label,
            transform=ax.transAxes,
            fontsize=mpl.rcParams["font.size"] + 1.5,
            fontweight="bold",
            va="bottom",
            ha="left",
        )


def audit_figure(fig, min_text_pt: float = 6.5) -> list[dict]:
    """Return machine-detectable figure issues; visual review is still required."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    issues: list[dict] = []
    canvas = fig.bbox

    for index, ax in enumerate(fig.axes):
        if not ax.get_visible() or not ax.axison:
            continue
        # Colorbar axes are labeled by the colorbar itself and need no x label.
        is_colorbar = ax.get_label() == "<colorbar>" or hasattr(ax, "_colorbar")
        if ax.has_data() and not is_colorbar:
            if not ax.get_xlabel().strip():
                issues.append({"severity": "error", "code": "missing-x-label", "axes": index})
            if not ax.get_ylabel().strip():
                issues.append({"severity": "error", "code": "missing-y-label", "axes": index})

        tick_boxes = []
        for text in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
            if not text.get_visible() or not text.get_text().strip():
                continue
            if text.get_fontsize() < min_text_pt:
                issues.append(
                    {
                        "severity": "error",
                        "code": "text-too-small",
                        "axes": index,
                        "text": text.get_text(),
                        "font_pt": text.get_fontsize(),
                    }
                )
            tick_boxes.append(text.get_window_extent(renderer).expanded(0.96, 0.96))
        overlaps = sum(
            box_a.overlaps(box_b)
            for i, box_a in enumerate(tick_boxes)
            for box_b in tick_boxes[i + 1 :]
        )
        if overlaps:
            issues.append(
                {"severity": "warning", "code": "tick-label-overlap", "axes": index, "pairs": overlaps}
            )

    for text in fig.findobj(match=mpl.text.Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        if text.get_fontsize() < min_text_pt:
            issues.append(
                {
                    "severity": "error",
                    "code": "text-too-small",
                    "text": text.get_text(),
                    "font_pt": text.get_fontsize(),
                }
            )
        bounds = text.get_window_extent(renderer)
        tolerance = 3
        if (
            bounds.x0 < canvas.x0 - tolerance
            or bounds.y0 < canvas.y0 - tolerance
            or bounds.x1 > canvas.x1 + tolerance
            or bounds.y1 > canvas.y1 + tolerance
        ):
            issues.append(
                {"severity": "warning", "code": "text-outside-canvas", "text": text.get_text()}
            )

    # Deduplicate issues generated through both tick and global text scans.
    unique = []
    seen = set()
    for issue in issues:
        key = json.dumps(issue, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(issue)
    return unique


def export_figure(
    fig,
    basename: str | Path,
    *,
    formats: Sequence[str] = ("svg", "pdf", "png"),
    dpi: int = 300,
    grayscale: bool = True,
    close: bool = False,
) -> list[Path]:
    """Export editable vector masters plus exact-size raster previews."""
    basename = Path(basename)
    basename.parent.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for fmt in formats:
        fmt = fmt.lower().lstrip(".")
        if fmt in {"jpg", "jpeg"}:
            raise ValueError("JPEG is not accepted for scientific figure delivery")
        if fmt not in {"svg", "pdf", "png", "tif", "tiff"}:
            raise ValueError(f"Unsupported format: {fmt}")
        path = basename.with_suffix(f".{fmt}")
        kwargs = {"facecolor": "white"}
        if fmt in {"png", "tif", "tiff"}:
            kwargs["dpi"] = dpi
        fig.savefig(path, **kwargs)
        outputs.append(path)

    if grayscale:
        png_path = basename.with_suffix(".png")
        if not png_path.exists():
            fig.savefig(png_path, dpi=dpi, facecolor="white")
            outputs.append(png_path)
        try:
            from PIL import Image

            gray_path = basename.with_name(f"{basename.name}_grayscale.png")
            with Image.open(png_path) as image:
                image.convert("L").convert("RGB").save(gray_path, dpi=(dpi, dpi))
            outputs.append(gray_path)
        except ImportError:
            pass
    if close:
        plt.close(fig)
    return outputs


def save_qa_report(fig, path: str | Path, min_text_pt: float = 6.5) -> dict:
    """Write audit results to JSON and return the report."""
    issues = audit_figure(fig, min_text_pt=min_text_pt)
    report = {
        "status": "failed" if any(item["severity"] == "error" for item in issues) else "passed",
        "visual_review_required": True,
        "issues": issues,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
