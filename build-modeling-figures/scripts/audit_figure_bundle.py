"""Audit a modeling figure contract, evidence files, exports, and QA record."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PLACEHOLDERS = {"", "todo", "tbd", "none", "null", "n/a", "待补充", "待定"}
REQUIRED_TEXT = (
    "id",
    "core_message",
    "reader_question",
    "paper_role",
    "archetype",
    "backend",
    "source_script",
    "deterministic_command",
    "hero_evidence",
)
REQUIRED_STATS = (
    "metric",
    "unit",
    "baseline",
    "sample_or_runs",
    "uncertainty",
    "test_or_validation",
)


def _is_placeholder(value) -> bool:
    return value is None or str(value).strip().lower() in PLACEHOLDERS


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _issue(issues: list[dict], severity: str, code: str, message: str, figure: str = "") -> None:
    item = {"severity": severity, "code": code, "message": message}
    if figure:
        item["figure"] = figure
    issues.append(item)


def _audit_svg(path: Path, issues: list[dict], figure_id: str) -> None:
    content = path.read_text(encoding="utf-8", errors="replace")
    if "<text" not in content:
        _issue(
            issues,
            "error",
            "svg-text-not-editable",
            f"{path.name} contains no SVG text elements; labels may have been converted to paths.",
            figure_id,
        )
    if re.search(r"(?:data:image/jpeg|\.jpe?g[\"'])", content, flags=re.IGNORECASE):
        _issue(
            issues,
            "warning",
            "svg-contains-jpeg",
            f"{path.name} contains JPEG raster content.",
            figure_id,
        )


def _audit_pdf(path: Path, issues: list[dict], figure_id: str) -> None:
    content = path.read_bytes()
    if b"/Subtype /Type3" in content or b"/Subtype/Type3" in content:
        _issue(
            issues,
            "warning",
            "pdf-type3-font",
            f"{path.name} appears to contain Type 3 fonts; use TrueType/OpenType embedding.",
            figure_id,
        )


def _audit_png(
    path: Path,
    size_mm: dict,
    issues: list[dict],
    figure_id: str,
    minimum_dpi: int,
) -> None:
    try:
        from PIL import Image
    except ImportError:
        _issue(issues, "warning", "pillow-unavailable", "PNG resolution was not inspected.", figure_id)
        return
    with Image.open(path) as image:
        dpi = image.info.get("dpi")
        if not dpi:
            _issue(issues, "warning", "png-dpi-missing", f"{path.name} has no DPI metadata.", figure_id)
            return
        effective_dpi = min(float(dpi[0]), float(dpi[1]))
        if effective_dpi + 0.5 < minimum_dpi:
            _issue(
                issues,
                "error",
                "png-dpi-low",
                f"{path.name} is {effective_dpi:.1f} dpi; required minimum is {minimum_dpi} dpi.",
                figure_id,
            )
        if all(isinstance(size_mm.get(key), (int, float)) and size_mm[key] > 0 for key in ("width", "height")):
            expected = (
                size_mm["width"] / 25.4 * float(dpi[0]),
                size_mm["height"] / 25.4 * float(dpi[1]),
            )
            deviations = [abs(actual - target) / target for actual, target in zip(image.size, expected)]
            if max(deviations) > 0.08:
                _issue(
                    issues,
                    "error",
                    "png-final-size-mismatch",
                    f"{path.name} pixel dimensions do not match final_size_mm at embedded DPI.",
                    figure_id,
                )


def audit_contract(contract_path: Path, root: Path | None = None, minimum_dpi: int = 300) -> dict:
    contract_path = contract_path.resolve()
    root = (root or contract_path.parent).resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    issues: list[dict] = []
    checked_files: list[str] = [str(contract_path)]
    figures = contract.get("figures")
    if not isinstance(figures, list) or not figures:
        _issue(issues, "error", "figures-missing", "Contract has no figure entries.")
        figures = []

    for index, figure in enumerate(figures):
        figure_id = str(figure.get("id") or f"index-{index}")
        for field in REQUIRED_TEXT:
            if _is_placeholder(figure.get(field)):
                _issue(issues, "error", f"missing-{field}", f"Required field {field!r} is empty.", figure_id)

        size_mm = figure.get("final_size_mm") or {}
        if not all(isinstance(size_mm.get(key), (int, float)) and size_mm[key] > 0 for key in ("width", "height")):
            _issue(issues, "error", "invalid-final-size", "final_size_mm needs positive width and height.", figure_id)

        panels = figure.get("panels")
        if not isinstance(panels, list) or not panels:
            _issue(issues, "error", "panels-missing", "At least one panel contract is required.", figure_id)
        else:
            for panel in panels:
                for field in ("id", "job", "metric_or_content", "unique_evidence"):
                    if _is_placeholder(panel.get(field)):
                        _issue(
                            issues,
                            "error",
                            f"panel-missing-{field}",
                            f"Panel {panel.get('id', '?')} has no {field}.",
                            figure_id,
                        )

        statistics = figure.get("statistics") or {}
        for field in REQUIRED_STATS:
            if _is_placeholder(statistics.get(field)):
                _issue(
                    issues,
                    "error",
                    f"statistics-missing-{field}",
                    f"Statistics field {field!r} is empty.",
                    figure_id,
                )

        source_script = figure.get("source_script")
        if not _is_placeholder(source_script):
            script_path = _resolve(root, str(source_script))
            checked_files.append(str(script_path))
            if not script_path.is_file():
                _issue(issues, "error", "source-script-missing", f"Missing {script_path}.", figure_id)

        sources = figure.get("source_data")
        if not isinstance(sources, list) or not sources:
            _issue(issues, "error", "source-data-missing", "No source_data files are declared.", figure_id)
        else:
            for source in sources:
                source_path = _resolve(root, str(source))
                checked_files.append(str(source_path))
                if not source_path.is_file():
                    _issue(issues, "error", "source-data-file-missing", f"Missing {source_path}.", figure_id)

        exports = figure.get("exports")
        if not isinstance(exports, list) or not exports:
            _issue(issues, "error", "exports-missing", "No exports are declared.", figure_id)
            exports = []
        suffixes = {Path(str(item)).suffix.lower() for item in exports}
        if not suffixes.intersection({".svg", ".pdf"}):
            _issue(issues, "error", "vector-master-missing", "An SVG or PDF vector master is required.", figure_id)
        if ".png" not in suffixes:
            _issue(issues, "error", "png-preview-missing", "A PNG preview is required.", figure_id)
        if suffixes.intersection({".jpg", ".jpeg"}):
            _issue(issues, "error", "jpeg-forbidden", "JPEG is not accepted for figure delivery.", figure_id)

        for export in exports:
            export_path = _resolve(root, str(export))
            checked_files.append(str(export_path))
            if not export_path.is_file():
                _issue(issues, "error", "export-file-missing", f"Missing {export_path}.", figure_id)
                continue
            suffix = export_path.suffix.lower()
            if suffix == ".svg":
                _audit_svg(export_path, issues, figure_id)
            elif suffix == ".pdf":
                _audit_pdf(export_path, issues, figure_id)
            elif suffix == ".png" and "grayscale" not in export_path.stem.lower():
                _audit_png(export_path, size_mm, issues, figure_id, minimum_dpi)

        qa_report = figure.get("qa_report")
        if figure.get("qa_status") != "passed":
            _issue(
                issues,
                "error",
                "qa-status-not-passed",
                f"Figure contract qa_status is {figure.get('qa_status')!r}.",
                figure_id,
            )
        if _is_placeholder(qa_report):
            _issue(issues, "error", "qa-report-missing", "qa_report is not declared.", figure_id)
        else:
            qa_path = _resolve(root, str(qa_report))
            checked_files.append(str(qa_path))
            if not qa_path.is_file():
                _issue(issues, "error", "qa-report-file-missing", f"Missing {qa_path}.", figure_id)
            else:
                try:
                    qa = json.loads(qa_path.read_text(encoding="utf-8"))
                    if qa.get("status") != "passed":
                        _issue(issues, "error", "qa-not-passed", f"QA status is {qa.get('status')!r}.", figure_id)
                except (json.JSONDecodeError, OSError) as exc:
                    _issue(issues, "error", "qa-report-invalid", str(exc), figure_id)

        if figure.get("conceptual_or_ai_generated") and re.search(
            r"result|evidence|validation|结果|证据|验证", str(figure.get("paper_role", "")), flags=re.IGNORECASE
        ):
            _issue(
                issues,
                "error",
                "conceptual-used-as-empirical",
                "Conceptual/AI-generated artwork cannot serve as empirical result evidence.",
                figure_id,
            )

    errors = sum(item["severity"] == "error" for item in issues)
    warnings = sum(item["severity"] == "warning" for item in issues)
    return {
        "status": "failed" if errors else "passed",
        "contract": str(contract_path),
        "root": str(root),
        "summary": {"figures": len(figures), "errors": errors, "warnings": warnings},
        "issues": issues,
        "checked_files": sorted(set(checked_files)),
        "visual_review_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--minimum-dpi", type=int, default=300)
    parser.add_argument("--strict", action="store_true", help="Return exit code 2 if any error is found")
    args = parser.parse_args()
    report = audit_contract(args.contract, args.root, args.minimum_dpi)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered)
    return 2 if args.strict and report["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
