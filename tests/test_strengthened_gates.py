from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE = REPO_ROOT / "scripts" / "audit_decision_trace.py"
RENDER = REPO_ROOT / "scripts" / "render_frozen_results.py"
REGISTER = REPO_ROOT / "scripts" / "register_experiment.py"
BRIDGE = REPO_ROOT / "scripts" / "preflight_matlab_python_bridge.py"
CANDIDATE = REPO_ROOT / "scripts" / "audit_candidate_evidence.py"
ROUTER = REPO_ROOT / "scripts" / "resolve_required_gates.py"
RUN_EXPERIMENT = REPO_ROOT / "scripts" / "run_experiment.py"


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

    def test_candidate_audit_distinguishes_legacy_incomplete_and_invalid(self) -> None:
        candidate = load_module("candidate_audit", CANDIDATE)
        self.assertEqual(
            candidate.classify_issues(
                {"schema_version": "1.0"}, ["schema_version must be 1.1"]
            ),
            "legacy_schema",
        )
        self.assertEqual(
            candidate.classify_issues(
                {"schema_version": "1.1"}, ["robustness artifact is missing"]
            ),
            "incomplete_evidence",
        )
        self.assertEqual(
            candidate.classify_issues(
                {"schema_version": "1.1", "feasibility": {"status": "failed"}},
                ["feasibility.status must be passed"],
            ),
            "invalid_result",
        )

    def test_gate_router_defers_delivery_and_skips_irrelevant_checks(self) -> None:
        router = load_module("gate_router", ROUTER)
        explore = router.resolve(
            {
                "workflow_stage": "explore",
                "task_family": "scheduling",
                "features": {"path_dependent", "mixed_backend"},
                "delivery_profile": "cumcm-latex",
            }
        )
        required = {item["gate"] for item in explore["required_gates"]}
        deferred = {item["gate"] for item in explore["deferred_gates"]}
        self.assertIn("executed_baseline", required)
        self.assertNotIn("cumcm_latex_preflight", required)
        self.assertIn("cumcm_latex_preflight", deferred)
        self.assertIn("decision_trace", deferred)
        delivery = router.resolve(
            {
                "workflow_stage": "deliver",
                "task_family": "prediction",
                "features": {"tabular_data"},
                "delivery_profile": "cumcm-latex",
            }
        )
        delivery_required = {item["gate"] for item in delivery["required_gates"]}
        self.assertIn("cumcm_latex_preflight", delivery_required)
        self.assertNotIn("decision_trace", delivery_required)
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "project-state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "workflow_profile": "explore",
                        "delivery_profile": "cumcm-latex",
                    }
                ),
                encoding="utf-8",
            )
            updated = subprocess.run(
                [
                    sys.executable,
                    str(ROUTER),
                    "--project-state",
                    str(state_path),
                    "--profile",
                    "candidate",
                    "--update-project-state",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(updated.returncode, 0, updated.stdout + updated.stderr)
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))[
                    "workflow_stage"
                ],
                "validate",
            )

    def test_run_experiment_records_command_and_runtime_automatically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "planning" / "experiments.json"
            registry.parent.mkdir(parents=True)
            create = subprocess.run(
                [
                    sys.executable,
                    str(REGISTER),
                    str(registry),
                    "create",
                    "--id",
                    "E1",
                    "--experiment-family",
                    "fixture",
                    "--candidate-budget",
                    "3",
                    "--cumulative-candidate-budget",
                    "3",
                    "--adaptive-search-bias-notes",
                    "No adaptive search",
                    "--hypothesis",
                    "wrapper records output",
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
                    "stop",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            writer = root / "write_result.py"
            writer.write_text(
                "import json, os\n"
                "path = os.environ['MMS_RESULT_JSON']\n"
                "json.dump({'value': 1.5, 'feasible': True, 'fidelity': 'passed', "
                "'candidates_evaluated': 2, 'notes': 'wrapper fixture'}, open(path, 'w'))\n",
                encoding="utf-8",
            )
            result_json = root / "results" / "run.json"
            manifest = root / "audit" / "run-manifest.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUN_EXPERIMENT),
                    str(registry),
                    "--id",
                    "E1",
                    "--result-json",
                    str(result_json),
                    "--manifest-out",
                    str(manifest),
                    "--",
                    sys.executable,
                    str(writer),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "recorded")
            self.assertGreater(saved["runtime_minutes"], 0)
            self.assertEqual(
                json.loads(registry.read_text(encoding="utf-8"))["experiments"][0][
                    "runs"
                ][0]["candidates_evaluated"],
                2,
            )


if __name__ == "__main__":
    unittest.main()
