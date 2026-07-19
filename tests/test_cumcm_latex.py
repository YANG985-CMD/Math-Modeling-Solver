import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "scripts" / "audit_cumcm_latex.py"
TEMPLATE = ROOT / "assets" / "latex" / "cumcm-2026" / "paper.tex"


class CumcmLatexAuditTests(unittest.TestCase):
    def run_audit(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AUDITOR), *arguments],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_bundled_template_passes_source_audit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "report.json"
            result = self.run_audit(
                str(TEMPLATE),
                "--allow-placeholders",
                "--json-out",
                str(report_path),
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["error_count"], 0)

    def test_detects_small_margins_toc_and_missing_graphic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_tex = Path(temp_dir) / "paper.tex"
            main_tex.write_text(
                r"""
\documentclass[a4paper]{ctexart}
\usepackage[margin=10mm]{geometry}
\usepackage{graphicx}
\begin{document}
\begin{abstract}摘要\end{abstract}
\textbf{关键词：}测试
\tableofcontents
\includegraphics{missing-figure}
\section{正文}\label{sec:one}
\begin{thebibliography}{9}\bibitem{a} A.\end{thebibliography}
\appendix\section{支撑材料文件清单}
\end{document}
""",
                encoding="utf-8",
            )
            result = self.run_audit(str(main_tex))
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            codes = {finding["code"] for finding in report["findings"]}
            self.assertTrue({"MARGIN_TOO_SMALL", "TOC_PRESENT", "MISSING_GRAPHIC"}.issubset(codes))

    def test_detects_duplicate_and_unresolved_labels(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            main_tex = Path(temp_dir) / "paper.tex"
            main_tex.write_text(
                r"""
\documentclass[a4paper]{ctexart}
\usepackage[top=25mm,bottom=25mm,left=25mm,right=25mm]{geometry}
\usepackage{fancyhdr}\cfoot{\thepage}
\begin{document}
\begin{abstract}摘要\end{abstract}\textbf{关键词：}测试
\section{正文}\label{dup}\label{dup} 见\ref{missing}。
\begin{thebibliography}{9}\bibitem{a} A.\end{thebibliography}
\appendix\section{支撑材料文件清单}
\end{document}
""",
                encoding="utf-8",
            )
            result = self.run_audit(str(main_tex))
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            codes = {finding["code"] for finding in report["findings"]}
            self.assertIn("DUPLICATE_LABEL", codes)
            self.assertIn("UNRESOLVED_LABEL", codes)

    def test_detects_oversized_support_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive = Path(temp_dir) / "support.rar"
            with archive.open("wb") as handle:
                handle.seek(20 * 1024 * 1024)
                handle.write(b"x")
            result = self.run_audit(
                str(TEMPLATE),
                "--allow-placeholders",
                "--support-archive",
                str(archive),
            )
            self.assertEqual(result.returncode, 2)
            report = json.loads(result.stdout)
            codes = {finding["code"] for finding in report["findings"]}
            self.assertIn("ARCHIVE_SIZE", codes)


if __name__ == "__main__":
    unittest.main()
