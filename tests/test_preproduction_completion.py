import unittest
from pathlib import Path
from tooling.contracts.validator import validate
from tooling.validation.preproduction import build_manifest,assert_drift_free

class PreproductionCompletionTests(unittest.TestCase):
    def test_review_binding_and_completion_manifest_validate(self):
        self.assertEqual(validate(Path("client-projects/reference-retail/experience/design/review-evidence-binding.yaml"),"review-evidence-binding"),[])
        self.assertEqual(validate(Path("client-projects/reference-retail/approved/preproduction-completion.yaml"),"preproduction-completion"),[])

    def test_reference_retail_is_complete_for_exactly_40_points(self):
        result=build_manifest("reference-retail")
        self.assertEqual(result["status"],"complete",result.get("blocking_items"))
        self.assertEqual([x["point"] for x in result["points"]],list(range(1,41)))
        self.assertTrue(all(x["status"]=="pass" for x in result["points"]))

    def test_completion_manifest_is_drift_free(self):
        self.assertEqual(assert_drift_free("reference-retail")["status"],"passed")

if __name__=="__main__":
    unittest.main()
