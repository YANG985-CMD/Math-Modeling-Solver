"""Build flat, editable modeling diagrams from a verified JSON specification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "assets" / "code" / "python"))

from modeling_plotkit import PALETTE, export_figure, setup_publication_style  # noqa: E402


NODE_COLORS = {
    "data": ("#E8F3F8", PALETTE["blue"]),
    "process": ("#EEF6F1", PALETTE["green"]),
    "model": ("#F1ECF6", PALETTE["purple"]),
    "decision": ("#FFF2E5", PALETTE["orange"]),
    "validation": ("#FDEBE6", PALETTE["vermillion"]),
    "output": ("#F2F2F2", PALETTE["black"]),
}


def _validate_spec(spec: dict) -> None:
    if spec.get("layout") not in {"pipeline", "layered", "closed_loop", "contrast"}:
        raise ValueError("layout must be pipeline, layered, closed_loop, or contrast")
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or len(nodes) < 2:
        raise ValueError("nodes must contain at least two items")
    ids = [node.get("id") for node in nodes]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("every node needs a unique, non-empty id")
    id_set = set(ids)
    for node in nodes:
        if not str(node.get("label", "")).strip():
            raise ValueError(f"node {node['id']!r} has no label")
    for edge in spec.get("edges", []):
        if edge.get("source") not in id_set or edge.get("target") not in id_set:
            raise ValueError(f"edge references an unknown node: {edge}")


def _positions(spec: dict) -> dict[str, tuple[float, float]]:
    nodes = spec["nodes"]
    layout = spec["layout"]
    if layout == "pipeline":
        xs = np.linspace(0.1, 0.9, len(nodes))
        return {node["id"]: (float(x), 0.52) for node, x in zip(nodes, xs)}
    if layout == "closed_loop":
        angles = np.linspace(np.pi, np.pi - 2 * np.pi, len(nodes), endpoint=False)
        return {
            node["id"]: (0.5 + 0.34 * np.cos(angle), 0.5 + 0.34 * np.sin(angle))
            for node, angle in zip(nodes, angles)
        }
    if layout == "contrast":
        groups = {}
        for node in nodes:
            groups.setdefault(str(node.get("group", "proposed")), []).append(node)
        if len(groups) != 2:
            raise ValueError("contrast layout requires exactly two node groups")
        positions = {}
        for x, (_, group_nodes) in zip((0.27, 0.73), groups.items()):
            ys = np.linspace(0.77, 0.27, len(group_nodes))
            positions.update({node["id"]: (x, float(y)) for node, y in zip(group_nodes, ys)})
        return positions

    layers = {}
    for node in nodes:
        layers.setdefault(int(node.get("layer", 0)), []).append(node)
    positions = {}
    ordered_layers = sorted(layers)
    ys = np.linspace(0.8, 0.24, len(ordered_layers))
    for y, layer in zip(ys, ordered_layers):
        layer_nodes = layers[layer]
        xs = np.linspace(0.15, 0.85, len(layer_nodes)) if len(layer_nodes) > 1 else [0.5]
        positions.update({node["id"]: (float(x), float(y)) for node, x in zip(layer_nodes, xs)})
    return positions


def _node_size(spec: dict) -> tuple[float, float]:
    count = len(spec["nodes"])
    if spec["layout"] == "pipeline":
        return (min(0.15, 0.7 / count), 0.16)
    if spec["layout"] == "closed_loop":
        return (0.18, 0.13)
    return (0.25, 0.13)


def draw_diagram(spec: dict):
    """Return a Matplotlib figure containing the specified diagram."""
    _validate_spec(spec)
    settings = setup_publication_style(
        spec.get("target", "competition"),
        spec.get("language", "zh"),
        spec.get("column", "double"),
        spec.get("size_mm", (180, 100)),
    )
    fig, ax = plt.subplots(
        figsize=tuple(value / 25.4 for value in settings["size_mm"]), constrained_layout=True
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    positions = _positions(spec)
    width, height = _node_size(spec)

    for edge in spec.get("edges", []):
        start = positions[edge["source"]]
        end = positions[edge["target"]]
        dx, dy = end[0] - start[0], end[1] - start[1]
        candidates = []
        if abs(dx) > 1e-9:
            candidates.append((width / 2) / abs(dx))
        if abs(dy) > 1e-9:
            candidates.append((height / 2) / abs(dy))
        boundary_t = min(candidates) if candidates else 0.0
        start_at = (start[0] + boundary_t * dx, start[1] + boundary_t * dy)
        end_at = (end[0] - boundary_t * dx, end[1] - boundary_t * dy)
        arrow = FancyArrowPatch(
            start_at,
            end_at,
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.05,
            color=PALETTE["gray"],
            connectionstyle=f"arc3,rad={float(edge.get('bend', 0))}",
            zorder=2,
        )
        ax.add_patch(arrow)
        label = str(edge.get("label", "")).strip()
        if label:
            mid_x, mid_y = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
            ax.text(
                mid_x,
                mid_y + 0.025,
                label,
                ha="center",
                va="center",
                fontsize=7.2,
                color=PALETTE["gray"],
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0, "alpha": 0.9},
                zorder=2,
            )

    for node in spec["nodes"]:
        x, y = positions[node["id"]]
        fill, edge = NODE_COLORS.get(node.get("kind", "process"), NODE_COLORS["process"])
        if node.get("accent"):
            edge = PALETTE["vermillion"]
        box = FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            facecolor=fill,
            edgecolor=edge,
            linewidth=1.8 if node.get("accent") else 1.05,
            zorder=3,
        )
        ax.add_patch(box)
        ax.text(
            x,
            y,
            str(node["label"]),
            ha="center",
            va="center",
            fontsize=8.2,
            fontweight="bold" if node.get("accent") else "normal",
            color=PALETTE["black"],
            wrap=True,
            zorder=4,
        )

    if spec.get("title"):
        ax.text(0.5, 0.97, str(spec["title"]), ha="center", va="top", fontsize=11, fontweight="bold")
    if spec.get("core_message"):
        ax.text(
            0.5,
            0.04,
            str(spec["core_message"]),
            ha="center",
            va="bottom",
            fontsize=7.5,
            color=PALETTE["gray"],
        )
    return fig


def demo_spec() -> dict:
    return {
        "schema_version": "1.0",
        "layout": "closed_loop",
        "target": "competition",
        "language": "zh",
        "column": "double",
        "size_mm": [180, 100],
        "title": "数据—模型—决策闭环",
        "core_message": "验证结果回流到数据与模型，形成可复现的迭代闭环",
        "nodes": [
            {"id": "data", "label": "数据审计", "kind": "data"},
            {"id": "features", "label": "特征与假设", "kind": "process"},
            {"id": "model", "label": "模型求解", "kind": "model", "accent": True},
            {"id": "decision", "label": "方案决策", "kind": "decision"},
            {"id": "validation", "label": "验证与稳健性", "kind": "validation"},
        ],
        "edges": [
            {"source": "data", "target": "features", "label": "可信数据"},
            {"source": "features", "target": "model", "label": "可检验假设"},
            {"source": "model", "target": "decision", "label": "候选解"},
            {"source": "decision", "target": "validation", "label": "待验证方案"},
            {"source": "validation", "target": "data", "label": "误差与新证据", "bend": -0.08},
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--spec", type=Path, help="Path to a diagram JSON specification")
    source.add_argument("--demo", action="store_true", help="Render the built-in closed-loop example")
    parser.add_argument("--out", type=Path, required=True, help="Output basename without extension")
    parser.add_argument("--no-grayscale", action="store_true")
    args = parser.parse_args()

    spec = demo_spec() if args.demo else json.loads(args.spec.read_text(encoding="utf-8"))
    fig = draw_diagram(spec)
    outputs = export_figure(fig, args.out.resolve(), grayscale=not args.no_grayscale, close=True)
    spec_out = args.out.resolve().with_name(f"{args.out.name}_spec.json")
    spec_out.parent.mkdir(parents=True, exist_ok=True)
    spec_out.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"spec": str(spec_out), "outputs": [str(p) for p in outputs]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
