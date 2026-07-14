from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


SKILL_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ASSETS = SKILL_ROOT / "assets" / "code" / "python"
sys.path.insert(0, str(PYTHON_ASSETS))

from demo_modeling_figure import build_demo
from modeling_plotkit import audit_figure, export_figure, new_figure


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


AUDITOR = load_module("figure_bundle_auditor", SKILL_ROOT / "scripts" / "audit_figure_bundle.py")
DIAGRAM = load_module("modeling_diagram", SKILL_ROOT / "scripts" / "build_modeling_diagram.py")


class FigureToolTests(unittest.TestCase):
    def test_audit_detects_missing_axis_labels(self) -> None:
        fig, ax = new_figure(target="competition", language="en", column="single")
        ax.plot([0, 1], [0, 1])
        issues = audit_figure(fig)
        codes = {item["code"] for item in issues}
        self.assertIn("missing-x-label", codes)
        self.assertIn("missing-y-label", codes)
        plt.close(fig)

    def test_export_keeps_svg_text_and_creates_grayscale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fig, ax = new_figure(target="competition", language="en", column="single")
            ax.plot([0, 1], [0, 1], label="Model")
            ax.set_xlabel("Input")
            ax.set_ylabel("Output")
            ax.legend()
            outputs = export_figure(fig, Path(directory) / "F1", close=True)
            names = {item.name for item in outputs}
            self.assertTrue({"F1.svg", "F1.pdf", "F1.png", "F1_grayscale.png"}.issubset(names))
            svg = (Path(directory) / "F1.svg").read_text(encoding="utf-8")
            self.assertIn("<text", svg)

    def test_demo_bundle_passes_strict_contract_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = build_demo(root)
            self.assertEqual(result["qa"]["status"], "passed", result["qa"])
            report = AUDITOR.audit_contract(result["contract"], root)
            self.assertEqual(report["status"], "passed", report)
            self.assertEqual(report["summary"]["errors"], 0)

            contract = json.loads(result["contract"].read_text(encoding="utf-8"))
            contract["figures"][0]["source_data"] = ["data/missing.csv"]
            result["contract"].write_text(json.dumps(contract), encoding="utf-8")
            rejected = AUDITOR.audit_contract(result["contract"], root)
            self.assertEqual(rejected["status"], "failed")
            self.assertTrue(any(item["code"] == "source-data-file-missing" for item in rejected["issues"]))

    def test_diagram_is_spec_driven_and_editable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fig = DIAGRAM.draw_diagram(DIAGRAM.demo_spec())
            outputs = export_figure(fig, Path(directory) / "D1", grayscale=True, close=True)
            self.assertTrue(any(item.suffix == ".svg" for item in outputs))
            svg = (Path(directory) / "D1.svg").read_text(encoding="utf-8")
            self.assertIn("<text", svg)
            self.assertIn("模型求解", svg)


if __name__ == "__main__":
    unittest.main()
