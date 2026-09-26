from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import yaml

from tooling.intelligence.best_practice_engine import build as build_best_practice
from tooling.experience.deep_reference import extract
from tooling.experience.direction_synthesis import build as build_directions
from tooling.experience.asset_intelligence import build as build_assets
from tooling.experience.visual_critic import evaluate as visual_critic
from tooling.review.authz import authorize, ReviewAuthError
from tooling.experience.penpot_automation import build_operations

class Phase1FinalGapTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.p=self.root/"client-projects"/"demo"
        for rel in [
            "derived","intelligence/research","experience/design/sources","experience/design",
            "experience/references","experience/qa","experience/directions"
        ]:
            (self.p/rel).mkdir(parents=True,exist_ok=True)
        self._write("derived/industry-profile.yaml",{"industry":"retail"})
        self._write("derived/capability-map.yaml",{"core":["catalogue","checkout"]})
        self._write("derived/truth-register.yaml",{"facts":[{"id":"f1"}],"assumptions":[],"unknowns":[],"conflicts":[]})
        self._write("intelligence/research/sources.yaml",{"sources":[
            {"id":"s1","ref":"https://example.test/a","captured_at":"2026-09-27T00:00:00Z","publisher":"Example","evidence":["catalogue","checkout"],"content_hash":"sha256:x"}
        ]})
        self._write("derived/journey-graph.yaml",{"journeys":[
            {"id":"browse-to-buy","actor":"customer","surfaces":["web-store"],"nodes":[
                {"id":"browse-to-buy.1","action":"browse","surface":"web-store","screen":"browse","capability":"catalogue","permission":"customer","backend_operation":"catalogue.read","success_state":"ready","error_state":"error","branches":[{"when":"success","next":[]}],"next":[]}
            ]}
        ]})
        self._write("derived/surface-map.yaml",{"required":["web-store"]})
        self._write("experience/references/adaptation.yaml",{"sources":[
            {"source_id":"ref1","ref":"https://ref","patterns":[{"id":"p1","decision":"ADAPT","reason":"fit","journeys":["browse-to-buy"]}]}
        ]})
        self._write("experience/synthesis.yaml",{"principles":["journey before screen"]})
        self._write("experience/design/source-inventory.yaml",{"sources":[{"id":"ref1","ref":"https://ref","assets":[{"ref":"https://ref/hero.jpg","license":"approved"}]}]})
        self._write("experience/design/sources/ref1.yaml",{"source_id":"ref1","type":"reference-site","provenance":{"content_hash":"sha256:a"},"components":[{"id":"c1","name":"ProductCard","type":"component","variants":["grid"]}],"patterns":[{"id":"p1","name":"product-grid"}],"tokens":{"spacing":"8"}})
        self._write("experience/design/theme-resolution.yaml",{"semantic_roles":{"surface.page":"#ffffff","surface.raised":"#f7f7f7","content.primary":"#111111","content.secondary":"#555555","action.primary":"#222222","feedback.error":"#aa0000"}})
        self._write("experience/design/design-ir.yaml",{"surfaces":["web-store"],"components":["product-card"],"journeys":[{"id":"browse-to-buy","nodes":[{"id":"browse-to-buy.1","surface":"web-store","component_refs":["product-card"],"state_refs":["default","loading","empty","failure"]}]}],"status":"review-ready"})
        self._write("experience/design/ui-implementation-registry.yaml",{"components":[{"semantic_id":"commerce.product-card","aliases":["product-card"],"penpot":{"component":"ProductCard"},"flutter":{"owned_component":"ProductCard","primitive":"x"},"web":{"owned_component":"ProductCard","primitive":"x"},"qa":{}}],"specialists":{},"registry_id":"r","version":1,"status":"review-ready"})
        self._write("experience/design/master-design-system.yaml",{"tokens":{"color":{}},"breakpoints":{"phone":0,"tablet":768,"desktop":1024,"wide":1440}})
    def tearDown(self):
        self.tmp.cleanup()
    def _write(self,rel,value):
        path=self.p/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(yaml.safe_dump(value,sort_keys=False),encoding="utf-8")

    def test_best_practice_is_evidence_backed(self):
        result=build_best_practice("demo",self.root)
        self.assertEqual(result["status"],"evidence-backed")
        self.assertEqual(result["source_count"],1)

    def test_deep_reference_preserves_evidence(self):
        record=yaml.safe_load((self.p/"experience/design/sources/ref1.yaml").read_text())
        result=extract(record)
        self.assertEqual(result["status"],"extracted")
        self.assertEqual(result["components"][0]["name"],"ProductCard")

    def test_directions_are_distinct_and_review_ready(self):
        out=build_directions("demo",self.root)
        self.assertEqual(set(out),{"A","B","C"})
        self.assertEqual(len({x["strategy"] for x in out.values()}),3)
        self.assertTrue(all(x["status"]=="review-ready" for x in out.values()))

    def test_asset_plan_uses_provenanced_asset(self):
        out=build_assets("demo",self.root)
        self.assertEqual(out["status"],"ready")
        self.assertEqual(out["requests"][0]["status"],"selected")

    def test_visual_critic_accepts_mapped_components(self):
        self._write("experience/design/asset-plan.yaml",build_assets("demo",self.root))
        out=visual_critic("demo",self.root)
        self.assertEqual(out["status"],"passed")

    def test_review_auth_binds_role_to_identity(self):
        with patch.dict(os.environ,{"REVIEW_MODE_WRITE_TOKEN":"secret"},clear=False):
            self.assertTrue(authorize("u","reviewer","comment","secret")["authorized"])
            with self.assertRaises(ReviewAuthError):
                authorize("u","reviewer","approve-experience","secret")

    def test_penpot_operations_include_components_and_journeys(self):
        out=build_operations("demo",self.root)
        self.assertEqual(out["client_id"],"demo")
        self.assertEqual(out["interactive_journeys"][0]["journey"],"browse-to-buy")

if __name__=="__main__":
    unittest.main()
