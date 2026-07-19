#!/usr/bin/env python3
"""Audit native Word math and a page-by-page Microsoft Word review manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
RAW_LATEX = re.compile(r"(?:\\(?:frac|sum|prod|int|sqrt|begin|end)\b|\$\$?)")


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def inside_file(root: Path, value: Any) -> Path | None:
    if not text(value):
        return None
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    path = path.expanduser().resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None
    return path if path.is_file() and path.stat().st_size > 0 else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_docx(path: Path) -> tuple[int, list[str]]:
    issues: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            document = archive.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError(f"invalid DOCX package: {exc}") from exc
    root = ElementTree.fromstring(document)
    math_count = len(root.findall(f".//{{{MATH_NS}}}oMath"))
    plain_text = "".join(root.itertext())
    if RAW_LATEX.search(plain_text):
        issues.append("raw LaTeX delimiters or commands remain in Word text")
    return math_count, issues


def audit(docx: Path, qa: dict[str, Any], root: Path, allow_no_math: bool) -> dict[str, Any]:
    issues: list[str] = []
    if docx.suffix.lower() != ".docx" or not docx.is_file():
        raise ValueError("input must be an existing DOCX file")
    math_count, docx_issues = inspect_docx(docx)
    issues.extend(docx_issues)
    if math_count < 1 and not allow_no_math:
        issues.append("DOCX contains no m:oMath native formula objects")
    if qa.get("schema_version") != "1.0":
        issues.append("QA schema_version must be 1.0")
    digest = sha256(docx)
    if qa.get("docx_sha256") != digest:
        issues.append("QA docx_sha256 does not match the audited document")
    if qa.get("rendered_with") != "Microsoft Word":
        issues.append("final visual QA must use Microsoft Word rendering")
    rendered_pdf = inside_file(root, qa.get("rendered_pdf"))
    if rendered_pdf is None or rendered_pdf.suffix.lower() != ".pdf":
        issues.append("rendered_pdf is missing, empty, outside the project, or not PDF")
    elif rendered_pdf.read_bytes()[:5] != b"%PDF-":
        issues.append("rendered_pdf does not have a PDF file signature")
    page_count = qa.get("page_count")
    reviewed_pages = qa.get("reviewed_pages")
    if not isinstance(page_count, int) or isinstance(page_count, bool) or page_count < 1:
        issues.append("page_count must be a positive integer")
    elif not isinstance(reviewed_pages, list) or reviewed_pages != list(
        range(1, page_count + 1)
    ):
        issues.append("reviewed_pages must list every page exactly once in order")
    if not text(qa.get("reviewed_by")) or not text(qa.get("reviewed_at")):
        issues.append("reviewed_by and reviewed_at are required")
    checks = qa.get("checks")
    if not isinstance(checks, dict):
        issues.append("checks must be an object")
    else:
        for name in ("formulas", "charts", "pagination", "encoding"):
            if checks.get(name) != "passed":
                issues.append(f"checks.{name} must be passed")
    return {
        "schema_version": "1.0",
        "status": "passed" if not issues else "failed",
        "docx": str(docx),
        "docx_sha256": digest,
        "omml_formula_count": math_count,
        "rendered_pdf": str(rendered_pdf) if rendered_pdf else "",
        "reviewed_page_count": len(reviewed_pages)
        if isinstance(reviewed_pages, list)
        else 0,
        "issue_count": len(issues),
        "issues": issues,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--qa-manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--allow-no-math", action="store_true")
    parser.add_argument("--out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        docx = args.docx.expanduser().resolve()
        qa_path = args.qa_manifest.expanduser().resolve()
        qa = json.loads(qa_path.read_text(encoding="utf-8-sig"))
        if not isinstance(qa, dict):
            raise ValueError("QA manifest must be a JSON object")
        root = (args.root or docx.parent).expanduser().resolve()
        result = audit(docx, qa, root, args.allow_no_math)
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0 if result["status"] == "passed" else 1
    except (OSError, json.JSONDecodeError, ValueError, ElementTree.ParseError) as exc:
        print(json.dumps({"status": "failed", "issues": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
