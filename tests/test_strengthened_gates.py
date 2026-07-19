from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE = REPO_ROOT / "scripts" / "audit_decision_trace.py"
WORD = REPO_ROOT / "scripts" / "audit_word_delivery.py"
RENDER = REPO_ROOT / "scripts" / "render_frozen_results.py"
REGISTER = REPO_ROOT / "scripts" / "register_experiment.py"
BRIDGE = REPO_ROOT / "scripts" / "preflight_matlab_python_bridge.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class StrengthenedGateTests(unittest.TestCase):
    def trace_fixture(self, root: Path) -> Path:
        (root / "baseline.json").write_text("{}\n", encoding="utf-8")
        (root / "intervention.json").write_text("{}\n", encoding="utf-8")

        def step(index: int, feasible: list[str], selected: str, score: float) -> dict:
            return {
                "step": index,
                "state_hash": f"state-{index}",
                "available_actions": ["A", "B"],
                "feasible_actions": feasible,
                "selected_action": selected,
                "score_after": score,
            }

        trace = {
            "schema_version": "1.0",
            "score_direction": "max",
            "baseline": {
                "id": "baseline",
                "artifact_path": "baseline.json",
                "final_score": 10,
                "steps": [step(1, ["A", "B"], "A", 4), step(2, ["A", "B"], "A", 10)],
            },
            "intervention": {
                "id": "guard",
                "artifact_path": "intervention.json",
                "final_score": 12,
                "steps": [step(1, ["A", "B"], "A", 4), step(2, ["B"], "B", 12)],
            },
        }
        path = root / "trace.json"
        path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
        return path

    def test_decision_trace_reports_first_divergence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace = self.trace_fixture(Path(directory))
            completed = subprocess.run(
                [sys.executable, str(TRACE), str(trace)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["first_filter_divergence_step"], 2)
            self.assertEqual(report["first_action_divergence_step"], 2)
            self.assertEqual(report["downstream_score_improvement"], 2)

    def test_decision_trace_rejects_action_outside_mask(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace = self.trace_fixture(Path(directory))
            value = json.loads(trace.read_text(encoding="utf-8"))
            value["intervention"]["steps"][1]["selected_action"] = "A"
            trace.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(TRACE), str(trace)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("selected_action is not feasible", completed.stdout)

    def test_frozen_results_renderer_uses_only_frozen_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "results" / "tables").mkdir(parents=True)
            artifact = root / "results" / "tables" / "scores.csv"
            artifact.write_text("name,score\nproposed,58.424\n", encoding="utf-8")
            frozen = root / "results" / "frozen-results.json"
            frozen.write_text(
                json.dumps(
                    {
                        "frozen": True,
                        "version": "v1",
                        "approved_by": "tester",
                        "metrics": [
                            {
                                "name": "score",
                                "baseline": 57.119,
                                "proposed": 58.424,
                                "artifact_path": "results/tables/scores.csv",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = root / "paper" / "generated.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RENDER),
                    str(frozen),
                    "--root",
                    str(root),
                    "--out",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("57.119", rendered)
            self.assertIn("58.424", rendered)
            self.assertIn("generated from frozen-results.json", rendered)

    def test_word_audit_requires_omml_and_complete_page_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docx = root / "report.docx"
            document_xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
 <w:body><w:p><m:oMath><m:r><m:t>x</m:t></m:r></m:oMath></w:p></w:body>
</w:document>"""
            with zipfile.ZipFile(docx, "w") as archive:
                archive.writestr("word/document.xml", document_xml)
            rendered_pdf = root / "report-rendered.pdf"
            rendered_pdf.write_bytes(b"%PDF-1.4\n% visual review fixture\n")
            digest = hashlib.sha256(docx.read_bytes()).hexdigest()
            qa = root / "word-qa.json"
            qa.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "docx_sha256": digest,
                        "rendered_with": "Microsoft Word",
                        "rendered_pdf": rendered_pdf.name,
                        "page_count": 2,
                        "reviewed_pages": [1, 2],
                        "reviewed_by": "tester",
                        "reviewed_at": "2026-07-19T00:00:00+08:00",
                        "checks": {
                            "formulas": "passed",
                            "charts": "passed",
                            "pagination": "passed",
                            "encoding": "passed",
                        },
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(WORD),
                    str(docx),
                    "--qa-manifest",
                    str(qa),
                    "--root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["omml_formula_count"], 1)

    def test_experiment_family_budget_cannot_be_reset_by_new_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "experiments.json"

            def create(experiment_id: str, candidate_budget: str, parent: str | None = None):
                command = [
                    sys.executable,
                    str(REGISTER),
                    str(registry),
                    "create",
                    "--id",
                    experiment_id,
                    "--experiment-family",
                    "one-family",
                    "--candidate-budget",
                    candidate_budget,
                    "--cumulative-candidate-budget",
                    "4",
                    "--adaptive-search-bias-notes",
                    "Earlier results may guide later choices",
                    "--hypothesis",
                    "bounded fixture",
                    "--metric",
                    "score",
                    "--direction",
                    "max",
                    "--baseline",
                    "1",
                    "--min-improvement",
                    "0.1",
                    "--max-runs",
                    "2",
                    "--max-runtime-minutes",
                    "5",
                    "--stop-condition",
                    "stop at budget",
                ]
                if parent:
                    command.extend(["--parent-experiment", parent])
                return subprocess.run(
                    command, capture_output=True, text=True, check=False
                )

            first = create("E1", "3")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            second = create("E2", "2", "E1")
            self.assertEqual(second.returncode, 2)
            self.assertIn("family candidate budget would be exceeded", second.stdout)

    def test_matlab_bridge_result_validator_distinguishes_array_failure(self) -> None:
        bridge = load_module("matlab_bridge", BRIDGE)
        valid = {
            "status": "passed",
            "scalar": bridge.SCALAR,
            "array": bridge.ARRAY,
            "unicode_token": "中文路径往返",
            "matlab_version": "R2024b",
        }
        self.assertEqual(bridge.verify_result(valid), [])
        invalid = dict(valid)
        invalid["array"] = [[1, 2, 3]]
        self.assertIn("array round trip failed", bridge.verify_result(invalid))


if __name__ == "__main__":
    unittest.main()
