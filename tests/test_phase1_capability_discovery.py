from pathlib import Path
import tempfile
import unittest

import yaml

from tooling.orchestrator.capabilities import discover


class CapabilityDiscoveryTests(unittest.TestCase):
    def test_discovers_existing_runtime_and_reports_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "client-projects" / "demo" / "derived").mkdir(parents=True)
            (root / "platform" / "capabilities").mkdir(parents=True)
            (root / "platform" / "commerce" / "medusa").mkdir(parents=True)

            (root / "client-projects" / "demo" / "derived" / "capability-map.yaml").write_text(
                yaml.safe_dump({
                    "mandatory": [],
                    "core": ["orders", "unknown-capability"],
                    "recommended": [],
                    "requested_additional": [],
                }),
                encoding="utf-8",
            )
            (root / "platform" / "capabilities" / "registry.yaml").write_text(
                yaml.safe_dump({
                    "version": 1,
                    "policy": {"reuse_actions": ["RETAIN", "UPGRADE", "BUILD"]},
                    "capabilities": {
                        "commerce": {
                            "runtime": "medusa",
                            "adapter": "platform/commerce/medusa/adapter.yaml",
                            "capabilities": ["orders"],
                        }
                    },
                }),
                encoding="utf-8",
            )
            (root / "platform" / "commerce" / "medusa" / "adapter.yaml").write_text(
                "provider: medusa\n", encoding="utf-8"
            )

            result = discover("demo", root)

            self.assertEqual(result["discovered"][0]["classification"], "RETAIN")
            self.assertEqual(result["unmapped_capabilities"], ["unknown-capability"])
            self.assertEqual(result["status"], "gaps-present")


if __name__ == "__main__":
    unittest.main()
