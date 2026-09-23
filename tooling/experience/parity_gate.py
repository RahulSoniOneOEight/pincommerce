from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    manifest = yaml.safe_load((root / "design-intelligence" / "pattern-expansion.yaml").read_text(encoding="utf-8"))
    flutter = (root / "packages/agency_flutter_ui/lib/agency_flutter_ui.dart").read_text(encoding="utf-8")
    web = (root / "packages/agency_web_ui/src/index.tsx").read_text(encoding="utf-8")
    blockers = []
    evidence = []
    for pattern_id, contract in manifest["patterns"].items():
        fs = contract["flutter"]
        ws = contract["web"]
        if f"class {fs}" not in flutter:
            blockers.append(f"{pattern_id}:flutter-symbol-missing")
        else:
            evidence.append(f"{pattern_id}:flutter")
        if f"function {ws}" not in web:
            blockers.append(f"{pattern_id}:web-symbol-missing")
        else:
            evidence.append(f"{pattern_id}:web")
        for field in ("states", "actions", "data_fields"):
            if not contract.get(field):
                blockers.append(f"{pattern_id}:{field}-contract-empty")
    return {
        "status": "passed" if not blockers else "blocked",
        "patterns": len(manifest["patterns"]),
        "evidence": evidence,
        "blocking_items": blockers,
        "rule": "behavioral contracts must exist on both runtimes; platform-native presentation differences are allowed",
    }


def main() -> int:
    result = evaluate()
    print(yaml.safe_dump(result, sort_keys=False))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
