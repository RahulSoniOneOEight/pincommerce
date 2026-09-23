from datetime import datetime, timezone
import unittest

from tooling.experience.dependency_intelligence import evaluate_dependencies
from tooling.experience.learning_loop import build_learning_signals
from tooling.experience.source_ingestion import ingest, merge_inventory


class Stage2DesignIntelligenceTests(unittest.TestCase):
    def test_figma_and_penpot_normalize_with_provenance(self):
        figma = ingest("figma", "figma-main", {"file_key": "abc", "components": [{"name": "ProductCard"}], "variables": {"radius": 12}}, captured_at="2026-09-23T00:00:00+00:00")
        penpot = ingest("penpot", "penpot-main", {"project_id": "p1", "components": [{"name": "QuickOrder"}], "tokens": {"space": 8}}, captured_at="2026-09-23T00:00:00+00:00")
        inventory = merge_inventory([figma, penpot])
        self.assertEqual(inventory["source_count"], 2)
        self.assertTrue(figma["provenance"]["content_hash"].startswith("sha256:"))

    def test_dependency_eligibility_blocks_stale_or_critical(self):
        policy = {"dependencies": {
            "license": {"allow": ["MIT"], "review": ["MPL-2.0"], "block": ["GPL-3.0", "unknown"]},
            "maintenance": {"healthy_max_days": 180, "watch_max_days": 365},
            "security": {"block_severity": "critical", "review_severities": ["high"]},
            "compatibility": {"required_fields": ["runtime", "version", "framework_compatibility"]},
            "rule": "visual preference cannot override eligibility",
        }}
        result = evaluate_dependencies([
            {"id": "good", "license": "MIT", "last_release_at": "2026-08-01T00:00:00Z", "runtime": "flutter", "version": "1.2.3", "framework_compatibility": "flutter>=3.22", "vulnerabilities": []},
            {"id": "bad", "license": "MIT", "last_release_at": "2024-01-01T00:00:00Z", "runtime": "web", "version": "2.0.0", "framework_compatibility": "react>=19", "vulnerabilities": [{"severity": "critical"}]},
        ], policy=policy, now=datetime(2026, 9, 23, tzinfo=timezone.utc))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["dependencies"][0]["eligibility"], "eligible")
        self.assertEqual(result["dependencies"][1]["eligibility"], "blocked")

    def test_learning_is_capped_advisory_and_requires_minimum_evidence(self):
        policy = {
            "minimum_observations": 3, "max_ranking_adjustment": 10,
            "accepted_weight": 2, "accepted_with_changes_weight": 1, "rejected_weight": -2,
            "telemetry": {"passed_weight": 2, "review_weight": 0, "failed_weight": -2},
            "guardrails": {"advisory_only": True, "requires_human_approval": True, "auto_promote": False, "mutate_approved_client_design": False},
        }
        result = build_learning_signals(
            [{"target": "product-card-a", "decision": "accepted"}, {"target": "product-card-a", "decision": "accepted"}, {"target": "product-card-a", "decision": "accepted-with-changes"}, {"target": "product-card-b", "decision": "accepted"}],
            [{"target": "product-card-a", "status": "passed"}],
            policy=policy,
        )
        by_target = {x["target"]: x for x in result["signals"]}
        self.assertGreater(by_target["product-card-a"]["ranking_adjustment"], 0)
        self.assertEqual(by_target["product-card-b"]["ranking_adjustment"], 0)
        self.assertFalse(result["guardrails"]["auto_promote"])


if __name__ == "__main__":
    unittest.main()
