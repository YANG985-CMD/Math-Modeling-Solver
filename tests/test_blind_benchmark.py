from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from blind_modeling_benchmark import (  # noqa: E402
    BenchmarkError,
    freeze_response,
    prepare_suite,
    score_benchmark,
    validate_frozen,
)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


class BlindBenchmarkTests(unittest.TestCase):
    def build_contracts(self, root: Path) -> tuple[Path, str, dict, dict]:
        statement = root / "statement.txt"
        statement.write_text("Problem statement only", encoding="utf-8")
        digest = hashlib.sha256(statement.read_bytes()).hexdigest()
        suite = {
            "schema_version": "1.0",
            "suite_id": "test-suite",
            "cases": [
                {
                    "case_id": "case-1",
                    "title": "Test case",
                    "declared_subproblem_ids": ["q1"],
                    "materials": [
                        {
                            "role": "statement",
                            "file_name": "statement.txt",
                            "url": statement.as_uri(),
                            "sha256": digest,
                            "redistribution": "external-only",
                        }
                    ],
                }
            ],
        }
        suite_path = root / "suite.json"
        write_json(suite_path, suite)
        response = {
            "schema_version": "1.0",
            "suite_id": "test-suite",
            "run_id": "run-1",
            "solution_materials_read": False,
            "blind_attestation": "Only declared materials were read.",
            "cases": [
                {
                    "case_id": "case-1",
                    "materials_read_sha256": [digest],
                    "subproblems": [
                        {
                            "id": "q1",
                            "objective": "Allocate resources feasibly.",
                            "task_families": ["resource-allocation"],
                            "baseline_families": ["linear-programming"],
                            "candidate_models": ["Linear program", "Robust program"],
                            "selected_model": "Start with the linear program.",
                            "validation_safeguards": [
                                "baseline-comparison",
                                "constraint-feasibility",
                            ],
                            "data_risks": ["missingness"],
                            "output_contract": "A feasible allocation table.",
                            "assumptions": [],
                        }
                    ],
                    "dependency_edges": [],
                    "unresolved_risks": [],
                }
            ],
        }
        rubric = {
            "schema_version": "1.0",
            "suite_id": "test-suite",
            "weights": {
                "routing": 0.35,
                "baseline": 0.2,
                "validation": 0.3,
                "data_risks": 0.15,
            },
            "cases": [
                {
                    "case_id": "case-1",
                    "subproblems": [
                        {
                            "id": "q1",
                            "required_task_families": ["resource-allocation"],
                            "accepted_task_families": [
                                "resource-allocation",
                                "multi-objective",
                            ],
                            "accepted_baseline_families": ["linear-programming"],
                            "required_validation_safeguards": [
                                "baseline-comparison",
                                "constraint-feasibility",
                            ],
                            "required_data_risks": ["missingness"],
                        }
                    ],
                }
            ],
        }
        return suite_path, digest, response, rubric

    def test_prepare_downloads_only_declared_material_and_verifies_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            suite_path, digest, _, _ = self.build_contracts(root)

            index = prepare_suite(suite_path, root / "prepared")

            copied = root / "prepared" / "case-1" / "statement.txt"
            self.assertTrue(copied.is_file())
            self.assertEqual(hashlib.sha256(copied.read_bytes()).hexdigest(), digest)
            self.assertEqual(index["cases"][0]["materials"][0]["role"], "statement")

            unsafe = json.loads(suite_path.read_text(encoding="utf-8"))
            unsafe["cases"][0]["case_id"] = "../escape"
            write_json(suite_path, unsafe)
            with self.assertRaises(BenchmarkError):
                prepare_suite(suite_path, root / "unsafe")

    def test_freeze_rejects_contamination_and_detects_later_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            suite_path, _, response, _ = self.build_contracts(root)
            response_path = root / "response.json"
            frozen_path = root / "frozen.json"
            write_json(response_path, response)

            frozen = freeze_response(suite_path, response_path, frozen_path)
            self.assertEqual(validate_frozen(frozen)["run_id"], "run-1")
            frozen["response"]["run_id"] = "changed"
            with self.assertRaises(BenchmarkError):
                validate_frozen(frozen)

            contaminated = copy.deepcopy(response)
            contaminated["solution_materials_read"] = True
            write_json(response_path, contaminated)
            with self.assertRaises(BenchmarkError):
                freeze_response(suite_path, response_path, root / "bad.json")

    def test_score_separates_accuracy_from_cross_run_stability(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            suite_path, _, response, rubric = self.build_contracts(root)
            rubric_path = root / "rubric.json"
            write_json(rubric_path, rubric)
            frozen_paths: list[Path] = []
            for index in (1, 2):
                current = copy.deepcopy(response)
                current["run_id"] = f"run-{index}"
                if index == 2:
                    subproblem = current["cases"][0]["subproblems"][0]
                    subproblem["task_families"] = ["multi-objective"]
                    subproblem["baseline_families"] = ["robust-optimization"]
                    subproblem["validation_safeguards"] = ["baseline-comparison"]
                    subproblem["data_risks"] = []
                response_path = root / f"response-{index}.json"
                frozen_path = root / f"frozen-{index}.json"
                write_json(response_path, current)
                freeze_response(suite_path, response_path, frozen_path)
                frozen_paths.append(frozen_path)

            report = score_benchmark(rubric_path, frozen_paths, root / "score")

            self.assertAlmostEqual(report["runs"][0]["score"], 1.0)
            self.assertLess(report["runs"][1]["score"], 0.5)
            self.assertLess(report["stability"]["overall"], 1.0)
            self.assertGreaterEqual(report["stability"]["overall"], 0.0)
            for name in (
                "blind-benchmark-report.json",
                "blind-benchmark-scores.csv",
                "blind-benchmark-dashboard.svg",
                "blind-benchmark-report.html",
            ):
                self.assertTrue((root / "score" / name).is_file())
            svg_path = root / "score" / "blind-benchmark-dashboard.svg"
            svg_root = ET.parse(svg_path).getroot()
            self.assertEqual(svg_root.attrib["viewBox"].split()[:2], ["0", "0"])
            svg_text = " ".join(svg_root.itertext())
            self.assertIn("各次独立运行正确率", svg_text)
            self.assertIn("跨运行稳定性", svg_text)
            self.assertIn("独立运行 1", svg_text)
            html_report = (root / "score" / "blind-benchmark-report.html").read_text(
                encoding="utf-8"
            )
            self.assertIn("blind-benchmark-dashboard.svg", html_report)

            single_report = score_benchmark(
                rubric_path, [frozen_paths[0]], root / "score-single"
            )
            self.assertIsNone(single_report["stability"]["overall"])
            single_svg = (
                root / "score-single" / "blind-benchmark-dashboard.svg"
            ).read_text(encoding="utf-8")
            self.assertIn(">不适用<", single_svg)


if __name__ == "__main__":
    unittest.main()
