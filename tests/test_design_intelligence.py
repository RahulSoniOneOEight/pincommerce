from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from tooling.experience.design_intelligence import build_design_intelligence
from tooling.experience.pexels_assets import search_photos


ROOT = Path(__file__).resolve().parents[1]


class DesignIntelligenceTests(unittest.TestCase):
    def test_reference_retail_selects_compact_multi_surface_stack(self):
        outputs = build_design_intelligence("reference-retail", ROOT)
        selection = outputs["experience/design/selection.yaml"]
        self.assertEqual(selection["preset"], "compact-commerce")
        self.assertIn("flutter", selection["platforms"])
        self.assertIn("web", selection["platforms"])
        self.assertEqual(selection["platforms"]["flutter"]["icons"], ["iconoir"])
        self.assertEqual(selection["platforms"]["web"]["icons"], ["iconoir"])
        patterns = {item["pattern"]: item for item in selection["patterns"]}
        self.assertIn("product-card", patterns)
        self.assertIn("b2b-quick-order", patterns)
        self.assertIn("dashboard-kpi", patterns)
        self.assertIn("exception-table", patterns)
        self.assertIn("data_table_2", patterns["b2b-quick-order"]["selected"]["flutter"])
        self.assertIn("tanstack_table", patterns["b2b-quick-order"]["selected"]["web"])

    def test_theme_resolves_semantic_roles_and_direction_overrides(self):
        outputs = build_design_intelligence("reference-retail", ROOT)
        theme = outputs["experience/design/theme-resolution.yaml"]
        self.assertIn("action.primary", theme["semantic_roles"])
        self.assertIn("border.default", theme["semantic_roles"])
        self.assertEqual(theme["overrides"]["direction_overrides"]["A"]["preset"], "premium-modern")
        self.assertEqual(theme["overrides"]["direction_overrides"]["B"]["preset"], "compact-commerce")

    def test_asset_plan_uses_client_assets_before_pexels(self):
        outputs = build_design_intelligence("reference-retail", ROOT)
        assets = outputs["experience/design/asset-plan.yaml"]
        self.assertEqual(assets["source_order"][0], "client-supplied")
        self.assertIn("pexels", assets["source_order"])
        self.assertTrue(assets["pexels"]["enabled"])
        self.assertTrue(all("pexels-if-missing" in item["provider_policy"] for item in assets["requests"]))

    @patch("urllib.request.urlopen")
    def test_pexels_search_normalizes_candidate_metadata(self, urlopen):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self):
                return b'{"photos":[{"id":123,"url":"https://pexels.com/photo/123","photographer":"A","photographer_url":"https://pexels.com/a","width":1200,"height":800,"alt":"Retail","src":{"large":"https://images/123.jpg"}}]}'
        urlopen.return_value = Response()
        result = search_photos("retail", api_key="test")
        self.assertEqual(result[0]["provider"], "pexels")
        self.assertEqual(result[0]["provider_asset_id"], "123")


if __name__ == "__main__":
    unittest.main()
