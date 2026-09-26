from pathlib import Path
import tempfile, unittest, yaml
from tooling.intelligence.phase1 import build_journey_graph, build_journey_capability_map

class Phase1IntelligenceTests(unittest.TestCase):
    def test_journey_nodes_map_to_existing_runtime_and_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); p=root/"client-projects"/"demo"
            (p/"derived").mkdir(parents=True)
            (p/"derived"/"journey-map.yaml").write_text(yaml.safe_dump({"journeys":[{"id":"browse-to-buy"}]}))
            (p/"derived"/"surface-map.yaml").write_text(yaml.safe_dump({"required":["customer-app"]}))
            (p/"derived"/"capability-map.yaml").write_text(yaml.safe_dump({"mandatory":[],"core":["catalogue","cart","checkout","orders"],"recommended":[],"requested_additional":[]}))
            graph=build_journey_graph("demo",root)
            self.assertEqual(graph["journeys"][0]["nodes"][0]["surface"],"customer-app")
            (p/"derived"/"journey-graph.yaml").write_text(yaml.safe_dump(graph))
            (p/"derived"/"capability-discovery.yaml").write_text(yaml.safe_dump({"discovered":[{"domain":"commerce","runtime":"medusa","matched_capabilities":["catalogue","cart","checkout","orders"],"classification":"RETAIN"}]}))
            mapped=build_journey_capability_map("demo",root)
            self.assertEqual(mapped["status"],"complete")
            self.assertTrue(all(x["runtime"]=="medusa" for x in mapped["mappings"]))

if __name__=="__main__": unittest.main()
