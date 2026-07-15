from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import savemat


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_dataset import audit_dataset  # noqa: E402


class DatasetAuditTests(unittest.TestCase):
    def issue_codes(self, report: dict) -> set[str]:
        return {issue["code"] for issue in report["issues"]}

    def test_csv_detects_quality_target_and_unit_risks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            frame = pd.DataFrame(
                {
                    "sample_id": list(range(20)),
                    "target": ["major"] * 18 + ["minor"] * 2,
                    "target_copy": ["major"] * 18 + ["minor"] * 2,
                    "constant": [7] * 20,
                    "score": list(range(19)) + [np.nan],
                    "mass": ["1kg", "2kg"] * 5 + ["100g", "200g"] * 5,
                }
            )
            frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
            input_path = root / "quality.csv"
            frame.to_csv(input_path, index=False, encoding="utf-8")

            report = audit_dataset([input_path], root / "audit", target="target")
            codes = self.issue_codes(report)

            self.assertIn("duplicate_rows", codes)
            self.assertIn("target_imbalance", codes)
            self.assertIn("target_copy_leakage", codes)
            self.assertIn("constant_column", codes)
            self.assertIn("mixed_units", codes)
            self.assertEqual(report["summary"]["files"], 1)
            self.assertEqual(report["summary"]["tables"], 1)
            self.assertEqual(report["tables"][0]["split_recommendation"]["strategy"], "stratified repeated cross-validation")
            fields = {field["column"]: field for field in report["tables"][0]["fields"]}
            self.assertEqual(fields["sample_id"]["semantic_type"], "identifier")

            for name in ("dataset-audit.json", "dataset-audit-fields.csv", "dataset-audit.html"):
                self.assertTrue((root / "audit" / name).is_file())
            persisted = json.loads((root / "audit" / "dataset-audit.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["schema_version"], "1.0")
            self.assertIn("html", persisted["outputs"])

    def test_time_and_group_leakage_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            frame = pd.DataFrame(
                {
                    "entity": ["A", "B", "A", "C", "D", "B"],
                    "when": [
                        "2024-01-04",
                        "2024-01-01",
                        "2024-01-02",
                        "2024-01-03",
                        "2024-01-05",
                        "2024-01-06",
                    ],
                    "split": ["train", "train", "test", "test", "test", "test"],
                    "target": [1, 2, 3, 4, 5, 6],
                    "post_event_value": [1, 2, 3, 4, 5, 6],
                }
            )
            input_path = root / "leakage.csv"
            frame.to_csv(input_path, index=False)

            report = audit_dataset(
                [input_path],
                root / "audit",
                target="target",
                time_column="when",
                group="entity",
                split="split",
            )
            codes = self.issue_codes(report)

            self.assertIn("time_not_ordered", codes)
            self.assertIn("temporal_split_overlap", codes)
            self.assertIn("group_split_leakage", codes)
            self.assertIn("target_copy_leakage", codes)
            self.assertEqual(
                report["tables"][0]["split_recommendation"]["strategy"],
                "group-aware rolling validation",
            )

    def test_excel_audits_all_sheets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "multi.xlsx"
            with pd.ExcelWriter(input_path, engine="openpyxl") as writer:
                pd.DataFrame({"x": [1, 2], "y": [3, 4]}).to_excel(
                    writer, sheet_name="observations", index=False
                )
                pd.DataFrame({"city": ["甲", "乙"], "value": [5, 6]}).to_excel(
                    writer, sheet_name="locations", index=False
                )

            report = audit_dataset([input_path], root / "audit")

            self.assertEqual(report["summary"]["tables"], 2)
            self.assertEqual(
                {table["table_name"] for table in report["tables"]},
                {"observations", "locations"},
            )

    def test_mat_audits_matrices_and_flags_undeclared_high_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            input_path = root / "arrays.mat"
            savemat(
                input_path,
                {
                    "features": np.arange(12, dtype=float).reshape(4, 3),
                    "labels": np.array([[0], [1], [1], [0]]),
                    "spectrum": np.array([[1 + 2j, 2 - 1j], [3 + 4j, -1j]]),
                    "cube": np.zeros((2, 3, 4)),
                },
            )

            report = audit_dataset([input_path], root / "audit")

            self.assertEqual(report["summary"]["tables"], 3)
            self.assertIn("unsupported_mat_dimension", self.issue_codes(report))
            self.assertIn("complex_numeric_fields", self.issue_codes(report))
            self.assertIn("high_dimensional_table", self.issue_codes(report))
            self.assertEqual(
                {table["table_name"] for table in report["tables"]},
                {"features", "labels", "spectrum"},
            )


if __name__ == "__main__":
    unittest.main()
