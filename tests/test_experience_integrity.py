from pathlib import Path
import tempfile
import unittest
import yaml

from tooling.experience.integrity import evaluate, _hash
from tooling.review.visual_qa import REQUIRED_CHECKS


class ExperienceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.p = self.root / "client-projects" / "c"
        for rel in ["derived", "experience/design", "experience/visual-qa"]:
            (self.p / rel).mkdir(parents=True, exist_ok=True)

        self.graph = {
            "client_id": "c",
            "journeys": [{
                "id": "buy",
                "surfaces": ["web"],
                "nodes": [
                    {"id": "buy.1", "surface": "web"},
                    {"id": "buy.2", "surface": "web"},
                ],
            }],
        }
        self.surface_map = {"required": ["web"]}
        self.design_ir = {
            "surfaces": ["web"],
            "components": ["card"],
            "journeys": [{
                "id": "buy",
                "nodes": [
                    {"id": "buy.1", "surface": "web", "component_refs": ["card"], "state_refs": ["default"]},
                    {"id": "buy.2", "surface": "web", "component_refs": ["card"], "state_refs": ["default"]},
                ],
            }],
            "status": "approved",
        }
        self.components = {"components": [{"id": "card"}], "status": "approved"}
        self.theme = {"semantic_roles": {"surface.page": "#fff"}}

        self._write("derived/journey-graph.yaml", self.graph)
        self._write("derived/surface-map.yaml", self.surface_map)
        self._write("experience/design/design-ir.yaml", self.design_ir)
        self._write("experience/design/component-contract-registry.yaml", self.components)
        self._write("experience/design/theme-resolution.yaml", self.theme)

        manifest = {
            "project_ref": "p",
            "revision_ref": "r1",
            "required_surfaces": ["web"],
            "required_journeys": ["buy"],
            "required_components": ["card"],
            "input_hashes": {
                "design_ir": _hash(self.design_ir),
                "components": _hash(self.components),
                "theme": _hash(self.theme),
                "journeys": _hash(self.graph),
            },
        }
        self._write("experience/design/penpot-manifest.yaml", manifest)
        self._write("experience/design/penpot-observed.yaml", {
            "project_ref": "p",
            "revision_ref": "r1",
            "components": ["card"],
            "interactive_journeys": ["buy"],
        })
        self._write("experience/visual-qa/VQA-web.yaml", {
            "surface": "web",
            "checks": [{"id": check, "status": "pass"} for check in REQUIRED_CHECKS],
            "status": "passed",
        })

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, rel, value):
        path = self.p / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

    def test_complete_chain_passes(self):
        result = evaluate("c", self.root)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["coverage"]["mapped_nodes"], 2)

    def test_stale_design_ir_blocks(self):
        changed = dict(self.design_ir)
        changed["surfaces"] = ["mobile"]
        self._write("experience/design/design-ir.yaml", changed)
        result = evaluate("c", self.root)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("Design IR surfaces differ" in x for x in result["blockers"]))
        self.assertTrue(any("Penpot manifest is stale" in x for x in result["blockers"]))

    def test_missing_design_node_blocks(self):
        changed = dict(self.design_ir)
        changed["journeys"] = [{
            "id": "buy",
            "nodes": [{"id": "buy.1", "surface": "web", "component_refs": ["card"], "state_refs": ["default"]}],
        }]
        self._write("experience/design/design-ir.yaml", changed)
        result = evaluate("c", self.root)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("Design IR nodes differ" in x for x in result["blockers"]))

    def test_incomplete_visual_qa_blocks(self):
        self._write("experience/visual-qa/VQA-web.yaml", {
            "surface": "web",
            "checks": [{"id": check, "status": "not-run"} for check in REQUIRED_CHECKS],
            "status": "review-ready",
        })
        result = evaluate("c", self.root)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("visual-qa web not passed" in x for x in result["blockers"]))


if __name__ == "__main__":
    unittest.main()
