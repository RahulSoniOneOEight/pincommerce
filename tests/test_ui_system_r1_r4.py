from pathlib import Path
import tempfile
import unittest
import yaml

from tooling.contracts.validator import validate_document
from tooling.experience.ui_resolver import resolve_component, resolve_icon, resolve_specialist, ResolverError
from tooling.experience.penpot_automation import build_operations
from tooling.experience.penpot_bridge import verify_manifest

ROOT=Path(__file__).resolve().parents[1]

class UISystemTests(unittest.TestCase):
    def test_platform_contracts_validate(self):
        pairs=[
            ("master-design-system","platform/ui/master-design-system.yaml"),
            ("ui-implementation-registry","platform/ui/implementation-registry.yaml"),
            ("icon-registry","platform/ui/icon-registry.yaml"),
            ("motion-registry","platform/ui/motion-registry.yaml"),
        ]
        for kind,rel in pairs:
            doc=yaml.safe_load((ROOT/rel).read_text(encoding="utf-8"))
            self.assertEqual(validate_document(doc,kind),[],kind)

    def test_component_resolver_is_deterministic(self):
        value=resolve_component("commerce.product-card","flutter",root=ROOT)
        self.assertEqual(value["flutter"]["owned_component"],"ProductCard")
        self.assertEqual(value["flutter"]["primitive"],"shadcn_flutter")
        web=resolve_component("data.table","web",root=ROOT)
        self.assertEqual(web["web"]["primitive"],"TanStack Table")

    def test_unknown_component_is_blocked(self):
        with self.assertRaises(ResolverError):
            resolve_component("invented.widget","web",root=ROOT)

    def test_specialists_and_icons(self):
        self.assertEqual(resolve_specialist("charts","flutter",root=ROOT),"fl_chart")
        icon=resolve_icon("commerce.cart","web",root=ROOT)
        self.assertEqual(icon["family"],"Phosphor")
        self.assertEqual(icon["web"]["symbol"],"ShoppingCart")

    def test_penpot_operations_include_responsive_states_and_journeys(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); p=root/"client-projects"/"c"
            (p/"experience"/"design").mkdir(parents=True)
            (p/"derived").mkdir(parents=True)
            docs={
              "experience/design/master-design-system.yaml":{"tokens":{"color":{"x":"y"}},"breakpoints":{"phone":0,"tablet":768,"desktop":1024,"wide":1440}},
              "experience/design/ui-implementation-registry.yaml":{"components":[{"semantic_id":"commerce.product-card","penpot":{"component":"ProductCard","variants":["mobile","web"]}}]},
              "experience/design/design-ir.yaml":{"journeys":[{"id":"buy","nodes":[{"id":"buy.1","surface":"web","component_refs":["commerce.product-card"],"state_refs":["default","loading","empty","failure"]}]}]},
              "derived/journey-graph.yaml":{"journeys":[{"id":"buy","nodes":[{"id":"buy.1","action":"select","next":[]}]}]},
            }
            for rel,value in docs.items():
                path=p/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(yaml.safe_dump(value),encoding="utf-8")
            out=build_operations("c",root)
            self.assertEqual(out["breakpoints"]["desktop"],1024)
            self.assertEqual(out["screens"][0]["states"],["default","loading","empty","failure"])
            self.assertEqual(out["interactive_journeys"][0]["journey"],"buy")

    def test_penpot_revision_mismatch_blocks(self):
        manifest={"project_ref":"p","revision_ref":"r1","required_components":[],"required_journeys":[]}
        errors=verify_manifest(manifest,{"project_ref":"p","revision_ref":"r2","components":[],"interactive_journeys":[]})
        self.assertTrue(errors)

if __name__=="__main__": unittest.main()
