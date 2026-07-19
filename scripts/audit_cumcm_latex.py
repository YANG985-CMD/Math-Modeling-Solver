#!/usr/bin/env python3
"""Audit CUMCM LaTeX source, compiled PDF, and optional support archive."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path


MAX_SUBMISSION_BYTES = 20 * 1024 * 1024
GRAPHIC_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".eps")


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    path: str = ""


def strip_comments(text: str) -> str:
    cleaned: list[str] = []
    for line in text.splitlines():
        cut = len(line)
        for index, char in enumerate(line):
            if char != "%":
                continue
            backslashes = 0
            cursor = index - 1
            while cursor >= 0 and line[cursor] == "\\":
                backslashes += 1
                cursor -= 1
            if backslashes % 2 == 0:
                cut = index
                break
        cleaned.append(line[:cut])
    return "\n".join(cleaned)


def load_tex_tree(main_tex: Path, findings: list[Finding]) -> dict[Path, str]:
    loaded: dict[Path, str] = {}

    def visit(path: Path) -> None:
        resolved = path.resolve()
        if resolved in loaded:
            return
        if not resolved.is_file():
            findings.append(Finding("error", "MISSING_TEX", f"Included TeX file is missing: {resolved}", str(resolved)))
            return
        text = resolved.read_text(encoding="utf-8-sig")
        cleaned = strip_comments(text)
        loaded[resolved] = cleaned
        for match in re.finditer(r"\\(?:input|include)\s*\{([^{}]+)\}", cleaned):
            target = match.group(1).strip()
            if "\\" in target or "#" in target:
                findings.append(Finding("warning", "DYNAMIC_TEX_INCLUDE", f"Cannot resolve dynamic include: {target}", str(resolved)))
                continue
            child = resolved.parent / target
            if child.suffix == "":
                child = child.with_suffix(".tex")
            visit(child)

    visit(main_tex)
    return loaded


def parse_length_mm(value: str) -> float | None:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*(mm|cm|in|pt)\s*", value)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2)
    return {
        "mm": number,
        "cm": number * 10.0,
        "in": number * 25.4,
        "pt": number * 25.4 / 72.27,
    }[unit]


def geometry_options(code: str) -> dict[str, str]:
    chunks = [m.group(1) for m in re.finditer(r"\\usepackage\s*\[([^\]]+)\]\s*\{geometry\}", code)]
    chunks.extend(m.group(1) for m in re.finditer(r"\\geometry\s*\{([^}]*)\}", code))
    values: dict[str, str] = {}
    for chunk in chunks:
        for item in chunk.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                values[key.strip().lower()] = value.strip()
            elif item.strip():
                values[item.strip().lower()] = "true"
    return values


def graphic_paths(code: str, main_dir: Path) -> list[Path]:
    paths = [main_dir, main_dir / "figures", main_dir / "images"]
    for match in re.finditer(r"\\graphicspath\s*\{((?:\{[^{}]+\})+)\}", code):
        for inner in re.findall(r"\{([^{}]+)\}", match.group(1)):
            paths.append((main_dir / inner).resolve())
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def asset_exists(target: str, bases: list[Path]) -> bool:
    raw = Path(target)
    suffixes = ("",) if raw.suffix else GRAPHIC_EXTENSIONS
    for base in bases:
        for suffix in suffixes:
            candidate = base / (target + suffix)
            if candidate.is_file():
                return True
    return False


def audit_source(main_tex: Path, allow_placeholders: bool, forbidden: list[str]) -> tuple[list[Finding], dict[Path, str]]:
    findings: list[Finding] = []
    sources = load_tex_tree(main_tex, findings)
    code = "\n".join(sources.values())
    lower_code = code.lower()

    documentclass = re.search(r"\\documentclass(?:\[([^\]]*)\])?\{([^}]+)\}", code)
    class_options = documentclass.group(1).lower() if documentclass and documentclass.group(1) else ""
    geometry = geometry_options(code)
    if "a4paper" not in class_options and "a4paper" not in geometry:
        findings.append(Finding("error", "PAGE_SIZE", "A4 paper is not explicitly configured.", str(main_tex)))

    if "margin" in geometry:
        for side in ("top", "bottom", "left", "right"):
            geometry.setdefault(side, geometry["margin"])
    missing_margins = [side for side in ("top", "bottom", "left", "right") if side not in geometry]
    if missing_margins:
        findings.append(Finding("warning", "MARGIN_UNVERIFIED", f"Margins are not explicit for: {', '.join(missing_margins)}", str(main_tex)))
    for side in ("top", "bottom", "left", "right"):
        if side not in geometry:
            continue
        value_mm = parse_length_mm(geometry[side])
        if value_mm is None:
            findings.append(Finding("warning", "MARGIN_UNPARSED", f"Could not parse {side} margin: {geometry[side]}", str(main_tex)))
        elif value_mm < 25.0 - 1e-6:
            findings.append(Finding("error", "MARGIN_TOO_SMALL", f"{side} margin is {value_mm:.2f} mm; minimum is 25 mm.", str(main_tex)))

    if re.search(r"\\tableofcontents\b", code):
        findings.append(Finding("error", "TOC_PRESENT", "The active source contains a table of contents.", str(main_tex)))

    abstract = re.search(r"\\begin\s*\{(?:abstract|cumcmabstract)\}", code)
    first_section = re.search(r"\\section\*?\s*\{", code)
    if not abstract:
        findings.append(Finding("error", "ABSTRACT_MISSING", "No abstract environment was found.", str(main_tex)))
    elif first_section and abstract.start() > first_section.start():
        findings.append(Finding("error", "ABSTRACT_ORDER", "The abstract must precede the main-text sections.", str(main_tex)))
    if not re.search(r"\\keywords\s*\{", code) and "关键词" not in code:
        findings.append(Finding("error", "KEYWORDS_MISSING", "No keywords field was found.", str(main_tex)))
    if not re.search(r"\\cfoot\s*\{\s*\\thepage\s*\}", code):
        findings.append(Finding("warning", "PAGE_NUMBER_UNVERIFIED", "Centered footer page numbering was not detected.", str(main_tex)))

    for command in ("author", "schoolname", "membera", "memberb", "memberc", "supervisor", "baominghao"):
        for match in re.finditer(rf"\\{command}\s*\{{([^}}]*)\}}", code, re.IGNORECASE):
            value = match.group(1).strip()
            if value:
                findings.append(Finding("error", "IDENTITY_FIELD", f"Non-empty identity command \\{command} was found.", str(main_tex)))

    for value in forbidden:
        if value and value.lower() in lower_code:
            findings.append(Finding("error", "FORBIDDEN_TEXT", f"Forbidden identity text appears in TeX source: {value}", str(main_tex)))

    if not allow_placeholders and (re.search(r"\[\[[^\]]+\]\]", code) or re.search(r"\\placeholder\s*\{", code)):
        findings.append(Finding("error", "PLACEHOLDER", "Unresolved template placeholders remain in the source.", str(main_tex)))

    bases = graphic_paths(code, main_tex.parent)
    for path, source in sources.items():
        local_bases = [path.parent, *bases]
        for match in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\s*\{([^{}]+)\}", source):
            target = match.group(1).strip()
            if "\\" in target or "#" in target:
                findings.append(Finding("warning", "DYNAMIC_GRAPHIC", f"Cannot resolve dynamic graphic: {target}", str(path)))
            elif not asset_exists(target, local_bases):
                findings.append(Finding("error", "MISSING_GRAPHIC", f"Graphic file is missing: {target}", str(path)))
        for match in re.finditer(r"\\lstinputlisting(?:\[[^\]]*\])?\s*\{([^{}]+)\}", source):
            target = match.group(1).strip()
            if "\\" not in target and "#" not in target and not (path.parent / target).is_file():
                findings.append(Finding("error", "MISSING_CODE_LISTING", f"Listed source file is missing: {target}", str(path)))

    labels = re.findall(r"\\label\s*\{([^{}]+)\}", code)
    for label in sorted(set(labels)):
        if labels.count(label) > 1:
            findings.append(Finding("error", "DUPLICATE_LABEL", f"Label is defined more than once: {label}", str(main_tex)))
    references = re.findall(r"\\(?:ref|eqref|cref|Cref)\s*\{([^{}]+)\}", code)
    for label in sorted(set(references) - set(labels)):
        findings.append(Finding("error", "UNRESOLVED_LABEL", f"Reference has no matching label: {label}", str(main_tex)))

    bibitems = re.findall(r"\\bibitem(?:\[[^\]]*\])?\s*\{([^{}]+)\}", code)
    for key in sorted(set(bibitems)):
        if bibitems.count(key) > 1:
            findings.append(Finding("error", "DUPLICATE_BIBITEM", f"Bibliography key is duplicated: {key}", str(main_tex)))
    if not bibitems and not re.search(r"\\(?:bibliography|printbibliography)\b", code):
        findings.append(Finding("error", "REFERENCES_MISSING", "No bibliography environment or bibliography command was found.", str(main_tex)))
    if "\\appendix" not in code:
        findings.append(Finding("error", "APPENDIX_MISSING", "No appendix command was found.", str(main_tex)))
    if "支撑材料文件清单" not in code:
        findings.append(Finding("error", "SUPPORT_MANIFEST_MISSING", "The appendix does not contain a supporting-material file list.", str(main_tex)))
    return findings, sources


def run_tool(executable: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([executable, *arguments], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)


def audit_pdf(pdf: Path, pdfinfo: str | None, pdftotext: str | None, body_pages: int | None, allow_placeholders: bool, forbidden: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    if not pdf.is_file():
        return [Finding("error", "PDF_MISSING", f"Compiled PDF is missing: {pdf}", str(pdf))]
    if pdf.stat().st_size > MAX_SUBMISSION_BYTES:
        findings.append(Finding("error", "PDF_SIZE", f"PDF size exceeds 20 MiB: {pdf.stat().st_size} bytes", str(pdf)))
    if body_pages is not None and body_pages > 30:
        findings.append(Finding("error", "BODY_PAGE_LIMIT", f"Main-text page count is {body_pages}; maximum is 30.", str(pdf)))

    info_exe = pdfinfo or shutil.which("pdfinfo")
    if not info_exe:
        findings.append(Finding("warning", "PDFINFO_UNAVAILABLE", "pdfinfo is unavailable; page geometry was not checked.", str(pdf)))
    else:
        try:
            result = run_tool(info_exe, [str(pdf)])
        except (OSError, subprocess.TimeoutExpired) as exc:
            findings.append(Finding("warning", "PDFINFO_FAILED", f"pdfinfo failed: {exc}", str(pdf)))
        else:
            if result.returncode != 0:
                findings.append(Finding("warning", "PDFINFO_FAILED", "pdfinfo could not inspect the PDF.", str(pdf)))
            else:
                match = re.search(r"Page size:\s*([0-9.]+)\s*x\s*([0-9.]+)\s*pts", result.stdout)
                if not match:
                    findings.append(Finding("warning", "PDF_PAGE_SIZE_UNPARSED", "Could not parse PDF page size.", str(pdf)))
                else:
                    width, height = float(match.group(1)), float(match.group(2))
                    a4 = (abs(width - 595.28) <= 4 and abs(height - 841.89) <= 4) or (abs(height - 595.28) <= 4 and abs(width - 841.89) <= 4)
                    if not a4:
                        findings.append(Finding("error", "PDF_NOT_A4", f"PDF page size is {width:.2f} x {height:.2f} pt, not A4.", str(pdf)))

    text_exe = pdftotext or shutil.which("pdftotext")
    if text_exe:
        try:
            result = run_tool(text_exe, ["-enc", "UTF-8", str(pdf), "-"])
        except (OSError, subprocess.TimeoutExpired):
            result = None
        if result and result.returncode == 0:
            extracted = result.stdout
            if "??" in extracted:
                findings.append(Finding("error", "UNRESOLVED_PDF_REFERENCE", "The PDF contains an unresolved '??' reference.", str(pdf)))
            if not allow_placeholders and (re.search(r"\[\[[^\]]+\]\]", extracted) or "【" in extracted):
                findings.append(Finding("error", "PDF_PLACEHOLDER", "The PDF contains unresolved template placeholders.", str(pdf)))
            for value in forbidden:
                if value and value.lower() in extracted.lower():
                    findings.append(Finding("error", "PDF_FORBIDDEN_TEXT", f"Forbidden identity text appears in the PDF: {value}", str(pdf)))
    return findings


def audit_log(log_path: Path | None) -> list[Finding]:
    if not log_path:
        return []
    if not log_path.is_file():
        return [Finding("warning", "LOG_MISSING", f"LaTeX log is missing: {log_path}", str(log_path))]
    text = log_path.read_text(encoding="utf-8", errors="replace")
    patterns = (
        "There were undefined references",
        "There were undefined citations",
        "multiply defined",
    )
    findings: list[Finding] = []
    for pattern in patterns:
        if pattern.lower() in text.lower():
            findings.append(Finding("error", "LATEX_LOG_REFERENCE", f"LaTeX log reports: {pattern}", str(log_path)))
    if re.search(r"LaTeX Warning: (?:Reference|Citation) .+ undefined", text):
        findings.append(Finding("error", "LATEX_LOG_REFERENCE", "LaTeX log contains undefined references or citations.", str(log_path)))
    return findings


def audit_archive(path: Path, forbidden: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    if not path.is_file():
        return [Finding("error", "ARCHIVE_MISSING", f"Support archive is missing: {path}", str(path))]
    if path.suffix.lower() not in {".zip", ".rar"}:
        findings.append(Finding("error", "ARCHIVE_FORMAT", "Support archive must use ZIP or RAR format.", str(path)))
    if path.stat().st_size > MAX_SUBMISSION_BYTES:
        findings.append(Finding("error", "ARCHIVE_SIZE", f"Support archive exceeds 20 MiB: {path.stat().st_size} bytes", str(path)))
    if path.suffix.lower() == ".zip" and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            names = "\n".join(archive.namelist()).lower()
        for value in forbidden:
            if value and value.lower() in names:
                findings.append(Finding("error", "ARCHIVE_FORBIDDEN_TEXT", f"Forbidden identity text appears in archive filenames: {value}", str(path)))
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("main_tex", type=Path)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--support-archive", type=Path)
    parser.add_argument("--body-pages", type=int)
    parser.add_argument("--forbidden-text", action="append", default=[])
    parser.add_argument("--allow-placeholders", action="store_true")
    parser.add_argument("--pdfinfo", help="Explicit pdfinfo executable")
    parser.add_argument("--pdftotext", help="Explicit pdftotext executable")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--strict", action="store_true", help="Return 1 when warnings remain")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    main_tex = args.main_tex.expanduser().resolve()
    if not main_tex.is_file():
        print(f"Main TeX file not found: {main_tex}", file=sys.stderr)
        return 2
    findings, sources = audit_source(main_tex, args.allow_placeholders, args.forbidden_text)
    if args.pdf:
        findings.extend(
            audit_pdf(
                args.pdf.expanduser().resolve(),
                args.pdfinfo,
                args.pdftotext,
                args.body_pages,
                args.allow_placeholders,
                args.forbidden_text,
            )
        )
    findings.extend(audit_log(args.log.expanduser().resolve() if args.log else None))
    if args.support_archive:
        findings.extend(audit_archive(args.support_archive.expanduser().resolve(), args.forbidden_text))

    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    report = {
        "schema_version": 1,
        "main_tex": str(main_tex),
        "source_files": [str(path) for path in sources],
        "error_count": errors,
        "warning_count": warnings,
        "findings": [asdict(item) for item in findings],
    }
    if args.json_out:
        output = args.json_out.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        return 2
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
