import tempfile,unittest,yaml
from pathlib import Path
from tooling.experience.component_registry import load_registry,apply
from tooling.experience.debt_gate import evaluate
from tooling.contracts.validator import validate
class ComponentGovernanceTests(unittest.TestCase):
    def test_selection_ledger_schema(self):
        self.assertEqual(validate(Path("client-projects/reference-retail/experience/design/selection-ledger.yaml"),"component-selection-ledger"),[])
    def test_registry_has_approved_lifecycle_records(self):
        doc=load_registry(); self.assertGreaterEqual(len(doc.get("lifecycle_records",{})),9)
        self.assertTrue(all(v["status"]=="approved" for v in doc["lifecycle_records"].values()))
    def test_registry_transition_requires_human_for_deprecation(self):
        doc=load_registry()
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"registry.yaml"; p.write_text(yaml.safe_dump(doc,sort_keys=False))
            cid=next(iter(doc["lifecycle_records"]))
            with self.assertRaises(ValueError): apply(cid,"deprecated",evidence=["replacement"],approver=None,path=p)
    def test_no_new_design_debt(self):
        self.assertEqual(evaluate()["status"],"passed")
if __name__=="__main__": unittest.main()
