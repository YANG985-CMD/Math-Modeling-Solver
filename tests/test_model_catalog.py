from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG = REPO_ROOT / "references" / "model-catalog.md"
RULES = REPO_ROOT / "references" / "model-routing-rules.json"


class ModelCatalogTests(unittest.TestCase):
    def load_rules(self) -> dict:
        return json.loads(RULES.read_text(encoding="utf-8"))

    def test_rules_have_evidence_aware_selection_policy(self) -> None:
        rules = self.load_rules()
        policy = rules["selection_policy"]
        self.assertTrue(policy["semantic_contract_first"])
        self.assertTrue(policy["baseline_must_run"])
        self.assertTrue(policy["upgrade_requires_named_failure"])
        self.assertEqual(policy["maximum_candidate_mechanisms"], 2)
        self.assertIn("generalization", policy["validation_claims_are_separate"])

    def test_task_families_are_structured_for_routing_and_falsification(self) -> None:
        rules = self.load_rules()
        families = rules["task_families"]
        self.assertGreaterEqual(len(families), 8)
        ids = [item["id"] for item in families]
        self.assertEqual(len(ids), len(set(ids)))
        for family in families:
            for field in (
                "baseline_models",
                "upgrade_models",
                "required_contract",
                "validation",
                "failure_signals",
                "risks",
            ):
                self.assertTrue(family[field], f"empty {field}: {family['id']}")

    def test_combination_patterns_require_separate_evidence(self) -> None:
        rules = self.load_rules()
        patterns = rules["combination_patterns"]
        self.assertGreaterEqual(len(patterns), 4)
        for pattern in patterns:
            self.assertGreaterEqual(len(pattern["components"]), 2)
            self.assertTrue(pattern["entry_condition"])
            self.assertTrue(pattern["required_evidence"])

    def test_catalog_blocks_keyword_only_and_complexity_only_selection(self) -> None:
        text = CATALOG.read_text(encoding="utf-8")
        self.assertIn("keywords alone", text)
        self.assertIn("baseline", text.lower())
        self.assertIn("hard-constraint", text)
        self.assertIn("Do not use LSTM/Transformer", text)
