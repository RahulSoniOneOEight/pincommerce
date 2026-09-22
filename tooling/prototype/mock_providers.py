from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


class MockProviderError(RuntimeError):
    pass


@dataclass
class MockProviderResponse:
    provider: str
    scenario: str
    success: bool
    payload: dict[str, Any]


class MockProviderRuntime:
    def __init__(self, catalog_path: Path | None = None):
        path = catalog_path or ROOT / "platform/prototype/mocks/provider-scenarios.yaml"
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.providers = value["providers"]

    def execute(self, provider: str, scenario: str, *, entity_id: str = "DEMO") -> MockProviderResponse:
        if provider not in self.providers:
            raise MockProviderError(f"Unknown mock provider: {provider}")
        scenarios = self.providers[provider]["scenarios"]
        if scenario not in scenarios:
            raise MockProviderError(f"Unknown scenario {scenario} for {provider}")
        configured = dict(scenarios[scenario])
        prefix = (
            configured.pop("external_id_prefix", None)
            or configured.pop("awb_prefix", None)
            or configured.pop("message_id_prefix", None)
        )
        if prefix:
            configured["external_id"] = f"{prefix}-{entity_id}"
        status = str(configured.get("status", "success"))
        success = status not in {"failed", "exception"}
        return MockProviderResponse(
            provider=provider,
            scenario=scenario,
            success=success,
            payload=configured,
        )
