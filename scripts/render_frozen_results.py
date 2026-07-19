#!/usr/bin/env python3
"""Render a manuscript-ready Markdown table from frozen canonical results."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def finite(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def escaped(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def number(value: float) -> str:
    return f"{float(value):.12g}"


def artifact(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("every frozen metric requires artifact_path")
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.expanduser().resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("metric artifact must stay inside the project root") from exc
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"metric artifact is missing or empty: {path}")
    return path


def render(value: dict[str, Any], root: Path, title: str) -> tuple[str, dict[str, Any]]:
    if value.get("frozen") is not True:
        raise ValueError("frozen-results.json must declare frozen: true")
    if not isinstance(value.get("version"), str) or not value["version"].strip():
        raise ValueError("frozen result version is missing")
    metrics = value.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        raise ValueError("frozen results must contain at least one metric")
    rows: list[str] = []
    manifest_metrics: list[dict[str, Any]] = []
    for index, metric in enumerate(metrics, 1):
        if not isinstance(metric, dict):
            raise ValueError(f"metrics[{index}] must be an object")
        name = metric.get("name")
        baseline = metric.get("baseline")
        proposed = metric.get("proposed")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"metrics[{index}].name is missing")
        if not finite(baseline) or not finite(proposed):
            raise ValueError(f"metrics[{index}] baseline and proposed must be finite")
        source = artifact(root, metric.get("artifact_path"))
        delta = float(proposed) - float(baseline)
        relative = source.relative_to(root.resolve()).as_posix()
        rows.append(
            "| "
            + " | ".join(
                [
                    escaped(name),
                    number(float(baseline)),
                    number(float(proposed)),
                    number(delta),
                    f"`{escaped(relative)}`",
                ]
            )
            + " |"
        )
        manifest_metrics.append(
            {
                "name": name,
                "baseline": float(baseline),
                "proposed": float(proposed),
                "delta": delta,
                "artifact_path": relative,
            }
        )
    markdown = (
        f"<!-- generated from frozen-results.json version {escaped(value['version'])}; do not edit -->\n"
        f"### {title}\n\n"
        "| 指标 | 基线 | 冻结结果 | 差值（冻结结果－基线） | 证据文件 |\n"
        "| --- | ---: | ---: | ---: | --- |\n"
        + "\n".join(rows)
        + "\n\n"
        + f"结果版本：`{escaped(value['version'])}`；批准人：{escaped(value.get('approved_by', ''))}。\n"
    )
    manifest = {
        "schema_version": "1.0",
        "source_version": value["version"],
        "metric_count": len(manifest_metrics),
        "metrics": manifest_metrics,
    }
    return markdown, manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frozen_results", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path)
    parser.add_argument("--title", default="冻结结果汇总")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        source = args.frozen_results.expanduser().resolve()
        value = json.loads(source.read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("frozen results must be a JSON object")
        root = (args.root or source.parent.parent).expanduser().resolve()
        markdown, manifest = render(value, root, args.title)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(markdown, encoding="utf-8", newline="\n")
        if args.manifest_out:
            args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
            args.manifest_out.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "failed", "issues": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
