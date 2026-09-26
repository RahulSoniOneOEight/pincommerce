from pathlib import Path
import tempfile, unittest, yaml
from unittest.mock import patch
from tooling.orchestrator.phase1_build import build_strategy, build_components, build_design_ir, critic, readiness

class Phase1BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.p=self.root/"client-projects"/"demo"
        (self.p/"derived").mkdir(parents=True); (self.p/"experience"/"design").mkdir(parents=True)
        (self.p/"derived"/"journey-graph.yaml").write_text(yaml.safe_dump({"journeys":[{"id":"browse-to-buy","nodes":[{"id":"browse-to-buy.1","surface":"customer-app","capability":"catalogue","error_state":"failed"}]},{"id":"order-tracking","nodes":[{"id":"order-tracking.1","surface":"customer-app","capability":"fulfilment","error_state":"failed"}]},{"id":"return-refund","nodes":[{"id":"return-refund.1","surface":"customer-app","capability":"return-refund","error_state":"failed"}]},{"id":"quote-to-order","nodes":[{"id":"quote-to-order.1","surface":"b2b","capability":"quote-rfq","error_state":"failed"}]}]}))
        (self.p/"derived"/"surface-map.yaml").write_text(yaml.safe_dump({"required":["customer-app","web-store","erp"]}))
    def tearDown(self): self.tmp.cleanup()
    def test_strategy_components_and_ir_are_connected(self):
        self.assertEqual(build_strategy("demo",self.root)["status"],"generated")
        reg=build_components("demo",self.root); self.assertTrue(reg["components"])
        ir=build_design_ir("demo",self.root); self.assertEqual(ir["journeys"][0]["nodes"][0]["component_refs"],["product-card"])
    def test_independent_critics_drive_integrated_gate(self):
        reg=build_components("demo",self.root); ir=build_design_ir("demo",self.root)
        (self.p/"experience"/"design"/"component-contract-registry.yaml").write_text(yaml.safe_dump(reg))
        (self.p/"experience"/"design"/"design-ir.yaml").write_text(yaml.safe_dump(ir))
        self.assertEqual(critic("demo","design",self.root)["status"],"passed")
        self.assertEqual(critic("demo","journey",self.root)["status"],"passed")
        with patch("tooling.orchestrator.phase1_build.assert_core_runtime_ready",return_value={}):
            self.assertEqual(readiness("demo",self.root)["status"],"integrated-prototype-ready")
if __name__=="__main__": unittest.main()
