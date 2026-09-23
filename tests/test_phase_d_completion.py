from __future__ import annotations

import copy
import unittest
from pathlib import Path

import yaml

from tooling.production.execution import evaluate_documents, evaluate_phase_d

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "client-projects" / "reference-retail"


def load(relative: str):
    return yaml.safe_load((PROJECT / relative).read_text(encoding="utf-8"))


class PhaseDCompletionTests(unittest.TestCase):
    def test_reference_retail_phase_d_is_complete(self):
        result = evaluate_phase_d("reference-retail", ROOT)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["blocking_items"], [])
        self.assertTrue(all(item["status"] == "pass" for item in result["checks"]))

    def test_provider_mismatch_blocks_d3(self):
        plan = load("production/production-plan.yaml")
        readiness = load("production/production-readiness.yaml")
        execution = load("production/production-execution.yaml")
        cross_domain = load("qa/cross-domain.yaml")
        production_qa = load("qa/production-qa.yaml")
        completion = load("production/phase-d-completion.yaml")
        broken = copy.deepcopy(execution)
        broken["provider_bindings"][0]["provider"] = "cashfree"
        result = evaluate_documents(plan, readiness, broken, cross_domain, production_qa, completion)
        self.assertEqual(result["status"], "blocked")
        d3 = next(item for item in result["checks"] if item["id"] == "d3-provider-bindings")
        self.assertEqual(d3["status"], "fail")

    def test_demo_data_promotion_blocks_d4(self):
        plan = load("production/production-plan.yaml")
        readiness = load("production/production-readiness.yaml")
        execution = load("production/production-execution.yaml")
        cross_domain = load("qa/cross-domain.yaml")
        production_qa = load("qa/production-qa.yaml")
        completion = load("production/phase-d-completion.yaml")
        broken = copy.deepcopy(execution)
        broken["migration"]["demo_data_replaced"] = False
        result = evaluate_documents(plan, readiness, broken, cross_domain, production_qa, completion)
        self.assertEqual(result["status"], "blocked")
        d4 = next(item for item in result["checks"] if item["id"] == "d4-migration-readiness")
        self.assertEqual(d4["status"], "fail")

    def test_placeholder_runtime_pin_blocks_d2(self):
        plan = load("production/production-plan.yaml")
        readiness = load("production/production-readiness.yaml")
        execution = load("production/production-execution.yaml")
        cross_domain = load("qa/cross-domain.yaml")
        production_qa = load("qa/production-qa.yaml")
        completion = load("production/phase-d-completion.yaml")
        broken = copy.deepcopy(execution)
        broken["runtimes"][0]["version"] = "<latest>"
        result = evaluate_documents(plan, readiness, broken, cross_domain, production_qa, completion)
        self.assertEqual(result["status"], "blocked")
        d2 = next(item for item in result["checks"] if item["id"] == "d2-runtime-provisioning-contract")
        self.assertEqual(d2["status"], "fail")


if __name__ == "__main__":
    unittest.main()
