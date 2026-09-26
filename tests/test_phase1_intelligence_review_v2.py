from pathlib import Path
import tempfile
import unittest
import yaml

from tooling.intelligence.input_intelligence import normalize_statements
from tooling.intelligence.journey_engine import build, validate_executable
from tooling.experience.reference_engine import apply_decisions
from tooling.experience.penpot_bridge import verify_manifest
from tooling.review.change_loop import ChangeLoopError

class IntelligenceV2Tests(unittest.TestCase):
    def test_input_classifies_unknowns_and_assumptions(self):
        out=normalize_statements("brief","Orders: 1000/month\nAssume growth: 10x\nRTO: TBD\n")
        self.assertEqual(len(out["facts"]),1)
        self.assertEqual(len(out["assumptions"]),1)
        self.assertEqual(len(out["unknowns"]),1)

    def test_multi_surface_journey(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); p=root/"client-projects"/"c"/"derived"; p.mkdir(parents=True)
            (p/"journey-map.yaml").write_text(yaml.safe_dump({"journeys":[{"id":"quote-to-order"}]}))
            (p/"surface-map.yaml").write_text(yaml.safe_dump({"required":["b2b","seller-portal","commerce-admin"]}))
            graph=build("c",root)
            self.assertEqual(validate_executable(graph),[])
            nodes=graph["journeys"][0]["nodes"]
            self.assertTrue(all("backend_operation" in n and "branches" in n for n in nodes))

    def test_reference_decisions_are_explicit(self):
        analysis={"client_id":"c","sources":[{"source_id":"s","ref":"x","patterns":[{"id":"p","name":"P","kind":"component","evidence":"P","journeys":["j"],"surfaces":["web"],"decision":None,"reason":"required","implementation_target":None}],"status":"analyzed"}],"blockers":[],"status":"analyzed"}
        out=apply_decisions(analysis,{"s":{"p":{"decision":"ADAPT","reason":"fit","implementation_target":"product-card"}}})
        self.assertEqual(out["status"],"evaluated")
        self.assertEqual(out["sources"][0]["patterns"][0]["decision"],"ADAPT")

    def test_penpot_verification_binds_revision(self):
        manifest={"project_ref":"p","revision_ref":"r1","required_components":["card"],"required_journeys":["buy"]}
        self.assertEqual(verify_manifest(manifest,{"project_ref":"p","revision_ref":"r1","components":["card"],"interactive_journeys":["buy"]}),[])
        self.assertTrue(verify_manifest(manifest,{"project_ref":"p","revision_ref":"r2","components":[],"interactive_journeys":[]}))

if __name__=="__main__": unittest.main()
