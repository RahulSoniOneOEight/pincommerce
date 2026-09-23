import json,tempfile,unittest
from pathlib import Path
from tooling.contracts.validator import validate
from tooling.experience.learning_orchestrator import assert_drift_free,run
from tooling.experience.visual_ai_provider import review_image
class Response:
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def read(self): return json.dumps({"findings":[{"severity":"minor","category":"spacing","message":"Review spacing"}]}).encode()
class ClosedLearningTests(unittest.TestCase):
    def test_connector_and_learning_ledgers_validate(self):
        self.assertEqual(validate(Path("client-projects/reference-retail/experience/design/connector-evidence.yaml"),"design-connector-evidence"),[])
        self.assertEqual(validate(Path("client-projects/reference-retail/experience/design/learning-ledger.yaml"),"design-learning-ledger"),[])
    def test_learning_run_is_drift_free_and_advisory(self):
        r=assert_drift_free("reference-retail"); self.assertEqual(r["status"],"passed")
        actual=run("reference-retail"); self.assertTrue(actual["requires_human_approval"]); self.assertFalse(actual["guardrails"]["auto_promote"])
    def test_visual_ai_provider_is_executable_but_advisory(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.png"; p.write_bytes(b"png")
            out=review_image(p,endpoint="https://visual.test",token="x",opener=lambda req,timeout=60:Response())
            self.assertFalse(out["approval_authority"])
if __name__=="__main__": unittest.main()
