from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INIT_SCRIPT = REPO_ROOT / "scripts" / "init_modeling_project.py"
AUDIT_SCRIPT = REPO_ROOT / "scripts" / "audit_modeling_project.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class WorkflowToolTests(unittest.TestCase):
    def test_initialized_project_fails_until_evidence_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            init = subprocess.run(
                [
                    sys.executable,
                    str(INIT_SCRIPT),
                    str(root),
                    "--mode",
                    "formal",
                    "--questions",
                    "2",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            audit = subprocess.run(
                [sys.executable, str(AUDIT_SCRIPT), str(root), "--no-write"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(audit.returncode, 1)
            report = json.loads(audit.stdout)
            self.assertEqual(report["gates"][0]["status"], "failed")
            self.assertEqual(report["gates"][1]["status"], "blocked")

    def test_complete_project_passes_all_gates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                [sys.executable, str(INIT_SCRIPT), str(root)],
                check=True,
                capture_output=True,
                text=True,
            )
            (root / "input" / "data.csv").write_text("x,y\n1,2\n", encoding="utf-8")
            (root / "src" / "model.py").write_text("print(1)\n", encoding="utf-8")
            (root / "results" / "tables" / "metrics.csv").write_text(
                "model,mae\nbaseline,2\nproposed,1\n", encoding="utf-8"
            )
            (root / "results" / "tables" / "robustness.csv").write_text(
                "seed,mae\n1,1.0\n2,1.1\n", encoding="utf-8"
            )

            contract = load_json(root / "planning" / "problem-contract.json")
            contract.update(
                {
                    "title": "Test",
                    "decision_to_support": "Select a forecast",
                    "time_budget": "24h",
                    "deliverables": ["forecast"],
                }
            )
            contract["subquestions"][0].update(
                {
                    "objective": "Forecast y",
                    "output_contract": "One forecast table",
                    "primary_metric": "MAE",
                }
            )
            write_json(root / "planning" / "problem-contract.json", contract)

            with (root / "planning" / "data-audit.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                fields = [
                    "input_id",
                    "path",
                    "source",
                    "retrieval_date",
                    "unit",
                    "provenance_verified",
                    "missingness_checked",
                    "outliers_checked",
                    "leakage_checked",
                    "notes",
                ]
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "input_id": "D001",
                        "path": "input/data.csv",
                        "source": "test fixture",
                        "retrieval_date": "2026-01-01",
                        "unit": "unitless",
                        "provenance_verified": "true",
                        "missingness_checked": "true",
                        "outliers_checked": "true",
                        "leakage_checked": "true",
                        "notes": "",
                    }
                )

            decision = load_json(root / "planning" / "method-decision.json")
            decision["questions"][0].update(
                {
                    "baseline": "mean",
                    "candidates": ["linear regression"],
                    "selected_method": "linear regression",
                    "validation_plan": "holdout MAE",
                    "user_decision": "approved",
                }
            )
            decision["questions"][0]["feasibility_probe"] = {
                "status": "passed",
                "artifact_path": "results/tables/metrics.csv",
                "finding": "runnable",
            }
            write_json(root / "planning" / "method-decision.json", decision)

            manifest = load_json(root / "audit" / "reproducibility-manifest.json")
            manifest.update(
                {
                    "executed": True,
                    "completed_at": "2026-01-01T00:00:00Z",
                    "command": "python src/model.py",
                    "source_files": ["src/model.py"],
                    "output_files": ["results/tables/metrics.csv"],
                }
            )
            manifest["environment"].update(
                {"os": "test", "language": "Python 3"}
            )
            write_json(root / "audit" / "reproducibility-manifest.json", manifest)

            frozen = load_json(root / "results" / "frozen-results.json")
            frozen.update(
                {
                    "frozen": True,
                    "version": "v1",
                    "approved_by": "tester",
                    "approved_at": "2026-01-01T00:00:00Z",
                    "metrics": [
                        {
                            "name": "MAE",
                            "baseline": 2,
                            "proposed": 1,
                            "artifact_path": "results/tables/metrics.csv",
                        }
                    ],
                    "validation_evidence": [
                        {
                            "type": "seed stability",
                            "artifact_path": "results/tables/robustness.csv",
                        }
                    ],
                }
            )
            write_json(root / "results" / "frozen-results.json", frozen)

            with (root / "audit" / "claim-evidence-ledger.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                fields = [
                    "claim_id",
                    "claim_text",
                    "scope",
                    "evidence_type",
                    "artifact_path",
                    "artifact_anchor",
                    "method_or_code",
                    "validation_status",
                    "limitations",
                    "status",
                ]
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                writer.writerow(
                    {
                        "claim_id": "C001",
                        "claim_text": "MAE decreased from 2 to 1",
                        "scope": "test",
                        "evidence_type": "table",
                        "artifact_path": "results/tables/metrics.csv",
                        "artifact_anchor": "rows 2-3",
                        "method_or_code": "src/model.py",
                        "validation_status": "passed",
                        "limitations": "fixture only",
                        "status": "verified",
                    }
                )

            manuscript = (
                "# Modeling Report\n\n"
                "frozen-results: v1\n\n"
                "## Abstract\n\nA reproducible fixture demonstrates the audit protocol. "
                "The proposed method is compared with a documented baseline.\n\n"
                "## Model\n\nThe implementation uses an explicit input contract, "
                "a baseline, and a deterministic execution record.\n\n"
                "## Results and Validation\n\nMAE decreased from 2 to 1 in the "
                "fixture. Seed stability evidence is linked in the claim ledger.\n\n"
                "## Limitations\n\nThis is a software test fixture, not an empirical claim.\n"
            )
            (root / "paper" / "main.md").write_text(manuscript, encoding="utf-8")

            audit = subprocess.run(
                [sys.executable, str(AUDIT_SCRIPT), str(root), "--no-write"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)
            report = json.loads(audit.stdout)
            self.assertEqual(report["overall_status"], "passed")
            self.assertTrue(all(gate["status"] == "passed" for gate in report["gates"]))


if __name__ == "__main__":
    unittest.main()
