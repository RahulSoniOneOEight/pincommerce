import tempfile, unittest, yaml
from pathlib import Path
from tooling.orchestrator.phase1_45 import (
    _reference_ok, _journey_graph_ok, _icons_motion_ok, _visual_qa_run,
    _critic_independent,
)
from tooling.review.visual_qa import REQUIRED_CHECKS

class Phase1QualityTests(unittest.TestCase):
    def test_reference_requires_reason(self):
        good = {"sources":[{"source_id":"s","patterns":[{"id":"p1","decision":"ADAPT","reason":"fits client","implementation_target":"PinProductCard"}]}]}
        self.assertTrue(_reference_ok(good))
        reuse_no_target = {"sources":[{"source_id":"s","patterns":[{"id":"p1","decision":"REUSE","reason":"client requirement"}]}]}
        self.assertTrue(_reference_ok(reuse_no_target))
        no_reason = {"sources":[{"source_id":"s","patterns":[{"id":"p1","decision":"ADAPT","reason":"","implementation_target":"x"}]}]}
        self.assertFalse(_reference_ok(no_reason))
        adapt_no_target = {"sources":[{"source_id":"s","patterns":[{"id":"p1","decision":"ADAPT","reason":"x"}]}]}
        self.assertFalse(_reference_ok(adapt_no_target))
        pending = {"sources":[{"source_id":"s","patterns":[{"id":"p1-pending-analysis","decision":"BUILD_NEW","reason":"x"}]}]}
        self.assertFalse(_reference_ok(pending))
        missing_decision = {"sources":[{"source_id":"s","patterns":[{"id":"p1","reason":"x"}]}]}
        self.assertFalse(_reference_ok(missing_decision))
        empty_patterns = {"sources":[{"source_id":"s","patterns":[]}]}
        self.assertFalse(_reference_ok(empty_patterns))

    def test_journey_rejects_stub_and_dead_next(self):
        stub = {"journeys":[{"id":"seller-onboarding","nodes":[
            {"id":"j.1","success_state":"ok","error_state":"err","next":[]}]}]}
        self.assertFalse(_journey_graph_ok(stub))
        good = {"journeys":[{"id":"buy","nodes":[
            {"id":"buy.1","success_state":"ok","error_state":"err","next":["buy.2"]},
            {"id":"buy.2","success_state":"ok","error_state":"err","next":[]},
        ]}]}
        self.assertTrue(_journey_graph_ok(good))
        dead = {"journeys":[{"id":"buy","nodes":[
            {"id":"buy.1","success_state":"ok","error_state":"err","next":["buy.99"]},
            {"id":"buy.2","success_state":"ok","error_state":"err","next":[]},
        ]}]}
        self.assertFalse(_journey_graph_ok(dead))

    def test_icons_motion_threshold(self):
        icons = {"icons":[{"semantic_id":f"i{n}"} for n in range(20)]}
        motions = {"motions":[{"semantic_id":f"m{n}"} for n in range(8)]}
        self.assertTrue(_icons_motion_ok(icons, motions))
        few_icons = {"icons":[{"semantic_id":"i1"}]}
        self.assertFalse(_icons_motion_ok(few_icons, motions))
        few_motions = {"motions":[{"semantic_id":"m1"}]}
        self.assertFalse(_icons_motion_ok(icons, few_motions))

    def test_critic_must_be_independent(self):
        self.assertTrue(_critic_independent({"status":"passed","reviewed_by":"reviewer"}))
        self.assertTrue(_critic_independent({"status":"passed","reviewer":"r"}))
        self.assertFalse(_critic_independent({"status":"passed"}))  # no reviewer = self-approved
        self.assertFalse(_critic_independent({"status":"blocked","reviewed_by":"r"}))

    def test_visual_qa_requires_every_mandatory_check_to_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            vqa = root/"experience"/"visual-qa"
            vqa.mkdir(parents=True)
            def y(rel):
                return yaml.safe_load((root/rel).read_text(encoding="utf-8"))
            partial={"checks":[{"id":check,"status":"pass" if i==0 else "not-run"} for i,check in enumerate(REQUIRED_CHECKS)],"status":"review-ready"}
            (vqa/"VQA-1.yaml").write_text(yaml.safe_dump(partial))
            self.assertFalse(_visual_qa_run(root, y))
            complete={"checks":[{"id":check,"status":"pass"} for check in REQUIRED_CHECKS],"status":"passed"}
            (vqa/"VQA-1.yaml").write_text(yaml.safe_dump(complete))
            self.assertTrue(_visual_qa_run(root, y))

if __name__ == "__main__":
    unittest.main()
