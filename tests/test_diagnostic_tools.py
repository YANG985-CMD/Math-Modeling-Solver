from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SCORE_SCRIPT = REPO_ROOT / "scripts" / "analyze_score_gap.py"
FIDELITY_SCRIPT = REPO_ROOT / "scripts" / "check_transition_fidelity.py"
SCORE = load_module("score_gap", SCORE_SCRIPT)
FIDELITY = load_module(
    "transition_fidelity", FIDELITY_SCRIPT
)
REGISTER = REPO_ROOT / "scripts" / "register_experiment.py"
PROMOTE = REPO_ROOT / "scripts" / "promote_validated_candidate.py"


class DiagnosticToolTests(unittest.TestCase):
    def test_score_gap_prioritizes_weighted_reference_gap(self) -> None:
        report = SCORE.diagnose(
            {
                "objective": "fixture",
                "components": [
                    {
                        "name": "quality",
                        "direction": "max",
                        "weight": 0.6,
                        "worst": 0,
                        "theoretical_best": 100,
                        "baseline": 50,
                        "reference": 75,
                    },
                    {
                        "name": "cost",
                        "direction": "min",
                        "weight": 0.4,
                        "worst": 100,
                        "theoretical_best": 0,
                        "baseline": 75,
                        "reference": 50,
                    },
                ],
            }
        )
        self.assertAlmostEqual(report["summary"]["baseline_weighted_score"], 0.4)
        self.assertAlmostEqual(report["summary"]["reference_weighted_score"], 0.65)
        self.assertAlmostEqual(report["summary"]["weighted_gap_to_reference"], 0.25)
        self.assertEqual(report["recommended_focus_basis"], "gap_to_reference")
        self.assertEqual(report["recommended_focus"][0], "quality")

    def test_score_gap_rejects_values_outside_declared_bounds(self) -> None:
        with self.assertRaises(SCORE.InputError):
            SCORE.diagnose(
                {
                    "components": [
                        {
                            "name": "invalid",
                            "direction": "max",
                            "weight": 1,
                            "worst": 0,
                            "theoretical_best": 10,
                            "baseline": 11,
                        }
                    ]
                }
            )

    @staticmethod
    def trajectory(count: int = 50) -> list[dict]:
        return [
            {
                "step": index,
                "time": float(index),
                "state": {"queue": index % 3, "position": [index, index + 1]},
                "action": "serve",
                "feasible_actions": ["serve", "hold"],
            }
            for index in range(count)
        ]

    def test_transition_fidelity_passes_identical_fifty_step_trace(self) -> None:
        trajectory = self.trajectory()
        report = FIDELITY.compare(trajectory, trajectory)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["summary"]["checked_steps"], 50)

    def test_transition_fidelity_catches_action_mask_failure(self) -> None:
        surrogate = self.trajectory()
        exact = self.trajectory()
        exact[12]["feasible_actions"] = ["hold"]
        report = FIDELITY.compare(surrogate, exact)
        self.assertEqual(report["status"], "failed")
        kinds = report["summary"]["mismatch_types"]
        self.assertIn("feasible_action_set_mismatch", kinds)
        self.assertIn("selected_action_infeasible_in_exact_simulator", kinds)

    def test_transition_fidelity_enforces_minimum_coverage(self) -> None:
        trajectory = self.trajectory(49)
        report = FIDELITY.compare(trajectory, trajectory)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["summary"]["coverage_passed"])

    def test_diagnostic_clis_write_inspectable_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            score_input = root / "score.json"
            score_input.write_text(
                json.dumps(
                    {
                        "components": [
                            {
                                "name": "score",
                                "direction": "max",
                                "weight": 1,
                                "worst": 0,
                                "theoretical_best": 100,
                                "baseline": 57.119,
                                "reference": 60,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            score_run = subprocess.run(
                [
                    sys.executable,
                    str(SCORE_SCRIPT),
                    str(score_input),
                    "--out-dir",
                    str(root / "score-output"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(score_run.returncode, 0, score_run.stdout + score_run.stderr)
            self.assertTrue((root / "score-output" / "score-gap-analysis.json").is_file())
            self.assertTrue((root / "score-output" / "score-gap-components.csv").is_file())

            trajectory = self.trajectory()
            surrogate = root / "surrogate.json"
            exact = root / "exact.json"
            surrogate.write_text(json.dumps(trajectory), encoding="utf-8")
            exact.write_text(json.dumps(trajectory), encoding="utf-8")
            fidelity_run = subprocess.run(
                [
                    sys.executable,
                    str(FIDELITY_SCRIPT),
                    str(surrogate),
                    str(exact),
                    "--out",
                    str(root / "fidelity.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                fidelity_run.returncode, 0, fidelity_run.stdout + fidelity_run.stderr
            )
            report = json.loads((root / "fidelity.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "passed")

    def test_experiment_lifecycle_requires_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry = root / "experiments.json"
            created = subprocess.run(
                [
                    sys.executable,
                    str(REGISTER),
                    str(registry),
                    "create",
                    "--id",
                    "E1",
                    "--hypothesis",
                    "A hard action mask improves feasible score",
                    "--metric",
                    "score",
                    "--direction",
                    "max",
                    "--baseline",
                    "50",
                    "--min-improvement",
                    "2",
                    "--max-runs",
                    "3",
                    "--max-runtime-minutes",
                    "10",
                    "--stop-condition",
                    "stop after three runs",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            recorded = subprocess.run(
                [
                    sys.executable,
                    str(REGISTER),
                    str(registry),
                    "record",
                    "--id",
                    "E1",
                    "--value",
                    "53",
                    "--feasible",
                    "--fidelity",
                    "passed",
                    "--artifact",
                    "results/E1.json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(recorded.returncode, 0, recorded.stdout + recorded.stderr)
            self.assertEqual(json.loads(registry.read_text(encoding="utf-8"))["experiments"][0]["status"], "candidate")

            missing = subprocess.run(
                [
                    sys.executable,
                    str(PROMOTE),
                    str(registry),
                    "--id",
                    "E1",
                    "--to",
                    "independently_validated",
                    "--evidence",
                    str(root / "missing.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(missing.returncode, 2)
            evidence = root / "independent-validation.json"
            evidence.write_text('{"status": "passed"}\n', encoding="utf-8")
            unstructured = subprocess.run(
                [
                    sys.executable,
                    str(PROMOTE),
                    str(registry),
                    "--id",
                    "E1",
                    "--to",
                    "independently_validated",
                    "--evidence",
                    str(evidence),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(unstructured.returncode, 2)

            artifact = root / "validation-artifact.txt"
            artifact.write_text("independent evidence\n", encoding="utf-8")
            report = {
                "schema_version": "1.0",
                "status": "passed",
                "primary_metric": {
                    "name": "score",
                    "direction": "max",
                    "baseline": 50,
                    "proposed": 53,
                    "minimum_improvement": 2,
                    "artifact_path": artifact.name,
                },
                "feasibility": {
                    "status": "passed",
                    "checks": ["all hard constraints"],
                    "artifact_path": artifact.name,
                },
                "fidelity": {"status": "not_required", "artifact_path": ""},
                "semantic_contract": {
                    "status": "passed",
                    "definitions": ["score is maximized on the declared test set"],
                    "artifact_path": artifact.name,
                },
                "support_and_identifiability": {
                    "status": "passed",
                    "summary": "three independent validation cases",
                    "limitations": [],
                    "artifact_path": artifact.name,
                },
                "structural_validity": {
                    "status": "passed",
                    "checks": [
                        {
                            "name": "state invariant",
                            "status": "passed",
                            "artifact_path": artifact.name,
                        }
                    ],
                },
                "robustness": {
                    "status": "passed",
                    "tested_cases": 3,
                    "artifact_path": artifact.name,
                },
                "multiobjective": {
                    "applicable": True,
                    "claim_type": "pareto_front",
                    "nondominated_points": 1,
                    "objective_spans": [[0, 1], [0, 1]],
                    "artifact_path": artifact.name,
                },
                "pipeline": {
                    "applicable": False,
                    "stage_checks": [],
                    "uncertainty_propagation": "",
                    "artifact_path": "",
                },
                "known_failure_regions": [],
                "claim_boundary": ["validated fixture only"],
            }
            evidence.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            thin_front = subprocess.run(
                [
                    sys.executable,
                    str(PROMOTE),
                    str(registry),
                    "--id",
                    "E1",
                    "--to",
                    "independently_validated",
                    "--evidence",
                    str(evidence),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(thin_front.returncode, 2)
            report["multiobjective"] = {
                "applicable": False,
                "claim_type": "not_applicable",
                "nondominated_points": 0,
                "objective_spans": [],
                "artifact_path": "",
            }
            evidence.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            promoted = subprocess.run(
                [
                    sys.executable,
                    str(PROMOTE),
                    str(registry),
                    "--id",
                    "E1",
                    "--to",
                    "independently_validated",
                    "--evidence",
                    str(evidence),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(promoted.returncode, 0, promoted.stdout + promoted.stderr)

    def test_later_lower_runs_do_not_demote_a_qualifying_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "experiments.json"
            created = subprocess.run(
                [
                    sys.executable,
                    str(REGISTER),
                    str(registry),
                    "create",
                    "--id",
                    "E1",
                    "--hypothesis",
                    "A bounded mechanism improves the score",
                    "--metric",
                    "score",
                    "--direction",
                    "max",
                    "--baseline",
                    "50",
                    "--min-improvement",
                    "2",
                    "--max-runs",
                    "3",
                    "--max-runtime-minutes",
                    "10",
                    "--stop-condition",
                    "stop after three runs",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            for run_id, value in (("R1", "53"), ("R2", "49"), ("R3", "48")):
                recorded = subprocess.run(
                    [
                        sys.executable,
                        str(REGISTER),
                        str(registry),
                        "record",
                        "--id",
                        "E1",
                        "--run-id",
                        run_id,
                        "--value",
                        value,
                        "--feasible",
                        "--fidelity",
                        "passed",
                        "--artifact",
                        f"results/{run_id}.json",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(recorded.returncode, 0, recorded.stdout + recorded.stderr)
            experiment = json.loads(registry.read_text(encoding="utf-8"))["experiments"][0]
            self.assertEqual(experiment["status"], "candidate")
            self.assertEqual(experiment["best_run"], "R1")


if __name__ == "__main__":
    unittest.main()
