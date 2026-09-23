from pathlib import Path
import unittest

import yaml

from tooling.experience.benchmark import build_benchmarks
from tooling.experience.dependency_health import evaluate_health
from tooling.experience.design_gates import component_ready
from tooling.experience.implementation_compiler import build_plan, scaffold_manifest
from tooling.experience.parity import compare_pattern_parity
from tooling.experience.source_import import normalize
from tooling.experience.theme_compiler import compile_theme

ROOT = Path(__file__).resolve().parents[1]


class AdvancedDesignIntelligenceTests(unittest.TestCase):
    def test_implementation_compiler_turns_selection_into_actions(self):
        plan = build_plan("reference-retail", ROOT)
        self.assertEqual(plan["status"], "ready")
        self.assertIn("flutter", plan["platforms"])
        self.assertIn("web", plan["platforms"])
        self.assertIn("data_table_2", plan["platforms"]["flutter"]["dependency_candidates"])
        self.assertIn("@tanstack/react-table", plan["platforms"]["web"]["dependency_candidates"])
        scaffold = scaffold_manifest(plan)
        targets = {item["target"] for item in scaffold["files"]}
        self.assertTrue(any("product_card.dart" in target for target in targets))
        self.assertTrue(any("product-card.tsx" in target for target in targets))

    def test_benchmark_plans_equal_fixture_tournaments(self):
        values = build_benchmarks("reference-retail", ROOT)
        self.assertTrue(values)
        product = next(item for item in values if item["pattern"] == "product-card")
        self.assertEqual(product["viewports"], ["mobile-390", "tablet-768", "desktop-1440"])
        self.assertIn("same-semantic-theme", product["capture_rules"])
        self.assertGreaterEqual(len(product["candidates"]), 2)

    def test_component_gate_requires_states_accessibility_and_performance(self):
        result = component_ready(
            required_states=["default", "loading", "error"],
            implemented_states=["default", "loading", "error"],
            accessibility={"checks": [
                {"id": "keyboard", "status": "pass"},
                {"id": "focus", "status": "pass"},
                {"id": "semantics", "status": "pass"},
                {"id": "contrast", "status": "pass"},
                {"id": "reduced-motion", "status": "pass"},
            ]},
            measurements={"frame_ms": 12},
            budgets={"frame_ms": 16},
        )
        self.assertEqual(result["status"], "passed")

    def test_component_gate_blocks_missing_state(self):
        result = component_ready(
            required_states=["default", "loading", "error"],
            implemented_states=["default", "loading"],
            accessibility={"checks": [
                {"id": "keyboard", "status": "pass"},
                {"id": "focus", "status": "pass"},
                {"id": "semantics", "status": "pass"},
                {"id": "contrast", "status": "pass"},
                {"id": "reduced-motion", "status": "pass"},
            ]},
            measurements={"frame_ms": 12},
            budgets={"frame_ms": 16},
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("missing-state:error", result["blocking_items"])

    def test_theme_compiler_creates_dark_variant_and_contrast_evidence(self):
        theme = yaml.safe_load(
            (ROOT / "client-projects/reference-retail/experience/design/theme-resolution.yaml").read_text()
        )
        result = compile_theme(theme)
        self.assertIn("dark", result)
        self.assertTrue(result["contrast_checks"])
        self.assertEqual(result["status"], "passed")

    def test_source_normalizer_preserves_figma_structure(self):
        result = normalize("figma", "client-figma", {
            "components": ["ProductCard"],
            "tokens": {"primary": "#123456"},
            "patterns": ["product-grid"],
        })
        self.assertEqual(result["type"], "figma")
        self.assertEqual(result["components"], ["ProductCard"])

    def test_health_blocks_stale_dependency(self):
        result = evaluate_health([
            {"id": "a", "license": "approved", "maintenance": "healthy", "security": "clear"},
            {"id": "b", "license": "approved", "maintenance": "stale", "security": "clear"},
        ])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["components"][1]["eligibility"], "blocked")

    def test_cross_platform_parity_allows_presentation_difference_not_behavior_gap(self):
        same = compare_pattern_parity(
            {"states": ["default"], "actions": ["buy"], "data_fields": ["price"], "error_states": ["error"]},
            {"states": ["default"], "actions": ["buy"], "data_fields": ["price"], "error_states": ["error"]},
        )
        self.assertEqual(same["status"], "passed")
        gap = compare_pattern_parity(
            {"states": ["default"], "actions": ["buy"], "data_fields": ["price"], "error_states": ["error"]},
            {"states": ["default"], "actions": [], "data_fields": ["price"], "error_states": ["error"]},
        )
        self.assertEqual(gap["status"], "review")


if __name__ == "__main__":
    unittest.main()
