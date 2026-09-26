from pathlib import Path
import tempfile, unittest, yaml
from tooling.experience.reference_patterns import extract_patterns, decide_patterns, ReferencePatternError
from tooling.contracts.validator import validate_document

class Phase145Tests(unittest.TestCase):
    def test_reference_patterns_never_invent(self):
        self.assertEqual(extract_patterns({"patterns":[],"components":[]}),[])
        with self.assertRaises(ReferencePatternError):
            decide_patterns({"source_id":"x","patterns":[]},journey_ids=["buy"],surfaces=["web"],decisions={})
    def test_reference_requires_explicit_decision(self):
        src={"source_id":"x","source_ref":"git:x","patterns":[{"id":"search","name":"Search"}]}
        with self.assertRaises(ReferencePatternError):
            decide_patterns(src,journey_ids=["buy"],surfaces=["web"],decisions={})
        d=decide_patterns(src,journey_ids=["buy"],surfaces=["web"],decisions={"search":"ADAPT"})
        self.assertEqual(d["patterns"][0]["decision"],"ADAPT")
    def test_review_contracts(self):
        pkg={"package_id":"DRP-demo-v1","client_id":"demo","design_revision":"v1","source_revision":"abc","penpot_ref":"penpot:p1","sections":[{"id":x,"title":x,"evidence_refs":["x"]} for x in ["overview","directions","design-system","screens","journeys","responsive","states","references","qa"]],"surface_refs":["web"],"journey_refs":["buy"],"qa_refs":["qa/x"],"status":"review-ready"}
        self.assertEqual(validate_document(pkg,"design-review-package"),[])
        approval={"approval_id":"EXP-demo-v1","client_id":"demo","review_package_ref":"experience/review/x.yaml","design_revision":"v1","source_revision":"abc","prototype_revision_ref":"experience/revisions/p.yaml","review_round_ref":"feedback/rounds/r.yaml","surface_decisions":[{"surface":"web","status":"approved"}],"journey_decisions":[{"journey":"buy","status":"approved"}],"decision":"approved","approved_by":"owner","approved_at":"2026-09-26T18:00:00+05:30","immutable":True}
        self.assertEqual(validate_document(approval,"experience-approval"),[])
if __name__=="__main__": unittest.main()
