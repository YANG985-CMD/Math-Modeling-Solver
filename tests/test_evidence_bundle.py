from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "scripts" / "init_evidence_bundle.py"
AUDIT = ROOT / "scripts" / "audit_evidence_bundle.py"


class EvidenceBundleTests(unittest.TestCase):
    def test_initializer_creates_registry_headers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = subprocess.run(
                [sys.executable, str(INIT), str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "results/result-registry.csv").is_file())
            with (root / "audit/figure-evidence.csv").open(encoding="utf-8", newline="") as handle:
                self.assertIn("figure_id", next(csv.reader(handle)))

    def test_audit_rejects_unhashed_paper_ready_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run([sys.executable, str(INIT), str(root)], check=True)
            artifact = root / "results" / "metric.json"
            artifact.write_text('{"mae": 1}\n', encoding="utf-8")
            with (root / "results/result-registry.csv").open("a", encoding="utf-8", newline="") as handle:
                csv.writer(handle).writerow(
                    ["R1", "Q1", "MAE", "1", "unit", "min", "results/metric.json", "", "RUN1", "passed", "paper_ready", "", "true", ""]
                )
            report = subprocess.run(
                [sys.executable, str(AUDIT), str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(report.returncode, 1)
            self.assertIn("artifact_sha256", report.stdout)

    def test_audit_accepts_frozen_result_with_passed_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run([sys.executable, str(INIT), str(root)], check=True)
            artifact = root / "results" / "metric.json"
            artifact.write_text('{"mae": 1}\n', encoding="utf-8")
            digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            with (root / "audit/run-record.csv").open("a", encoding="utf-8", newline="") as handle:
                csv.writer(handle).writerow(
                    ["RUN1", "Q1", "python src/model.py", str(root), "input/data.csv", "results/metric.json", "{}", "7", "python", "", "", "0", "passed", "audit/run.log"]
                )
            with (root / "results/result-registry.csv").open("a", encoding="utf-8", newline="") as handle:
                csv.writer(handle).writerow(
                    ["R1", "Q1", "MAE", "1", "unit", "min", "results/metric.json", digest, "RUN1", "passed", "frozen", "", "true", ""]
                )
            report = subprocess.run(
                [sys.executable, str(AUDIT), str(root)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(report.returncode, 0, report.stdout)
            self.assertEqual(json.loads(report.stdout)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
