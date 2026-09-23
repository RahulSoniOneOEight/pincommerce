from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate, validate_document
from tooling.experience.coverage import assert_client_review_ready
from tooling.experience.debt_gate import evaluate as evaluate_debt
from tooling.experience.learning_orchestrator import assert_drift_free as learning_drift
from tooling.validation.abc_seam import audit_client
from tooling.validation.preprototype import evaluate as preprototype_evaluate

ROOT = Path(__file__).resolve().parents[2]

POINTS: list[tuple[int, str, list[str]]] = [
    (1, "Client onboarding and truth capture", ["input/client-input.yaml", "derived/truth-register.yaml"]),
    (2, "Business-model and archetype intelligence", ["derived/classification-evidence.yaml", "derived/industry-profile.yaml", "derived/benchmark-report.yaml"]),
    (3, "Capability intelligence", ["derived/capability-gap.yaml", "derived/capability-gap-analysis.yaml", "derived/capability-map.yaml"]),
    (4, "Journey intelligence", ["derived/journey-map.yaml"]),
    (5, "Entity and data intelligence", ["derived/entity-map.yaml", "contracts/data-contract.yaml"]),
    (6, "Surface intelligence", ["derived/surface-map.yaml"]),
    (7, "Integration intelligence", ["derived/integration-map.yaml", "contracts/integration-contract.yaml"]),
    (8, "Architecture decisions", ["solution/solution-contract.yaml", "solution/decisions/ADR-reference-retail-001.yaml"]),
    (9, "Commerce runtime", ["experience/prototype-core-runtime.yaml", "@root/platform/commerce/medusa/adapter.yaml"]),
    (10, "Marketplace runtime", ["experience/prototype-core-runtime.yaml", "@root/platform/marketplace/mercur/adapter.yaml"]),
    (11, "ERP runtime", ["experience/prototype-core-runtime.yaml", "@root/platform/erp/tryton/adapter.yaml"]),
    (12, "Event and messaging layer", ["@root/platform/integration/event-catalog.yaml", "@root/tooling/integration/nats_transport.py"]),
    (13, "Search runtime", ["@root/platform/search/meilisearch/adapter.yaml"]),
    (14, "Integration runtime", ["contracts/integration-contract.yaml", "@root/tooling/integration/runtime.py", "@root/tooling/integration/reconciliation.py"]),
    (15, "Design-source intelligence", ["experience/design/source-inventory.yaml", "experience/design/connector-evidence.yaml"]),
    (16, "Component and library selection", ["experience/design/selection.yaml", "experience/design/selection-ledger.yaml"]),
    (17, "Theme and token system", ["contracts/design-contract.yaml", "@root/design-contract/tokens/foundation.yaml", "@root/design-contract/tokens/semantic.yaml"]),
    (18, "Semantic icons and motion", ["contracts/design-contract.yaml", "@root/design-intelligence/semantic-icons.yaml", "@root/design-intelligence/motion-tokens.yaml"]),
    (19, "Shared Flutter UI runtime", ["@root/packages/agency_flutter_ui/lib/agency_flutter_ui.dart"]),
    (20, "Shared web UI runtime", ["@root/packages/agency_web_ui/src/index.tsx"]),
    (21, "Governed component patterns", ["@root/design-intelligence/pattern-expansion.yaml", "@root/design-intelligence/component-registry.yaml"]),
    (22, "Widgetbook and Storybook catalogs", ["@root/apps/widgetbook/lib/main.dart", "@root/apps/storybook/stories/ProductCard.stories.tsx"]),
    (23, "Screenshot rendering", ["@root/design-intelligence/approved-visual-baselines.yaml", "@root/tooling/experience/web_evidence.mjs"]),
    (24, "Accessibility QA", ["@root/design-intelligence/accessibility-performance-policy.yaml", "@root/tooling/experience/visual_evidence.py"]),
    (25, "Performance QA", ["@root/design-intelligence/accessibility-performance-policy.yaml", "@root/design-intelligence/visual-evidence.yaml"]),
    (26, "Visual regression", ["@root/design-intelligence/approved-visual-baselines.yaml", "@root/tooling/experience/visual_baseline.py"]),
    (27, "A/B/C design tournament", ["experience/design/tournament.yaml", "@root/tooling/experience/visual_tournament.py"]),
    (28, "Visual AI QA", ["@root/tooling/experience/visual_ai_provider.py", "@root/tooling/experience/visual_ai_qa.py"]),
    (29, "Dependency intelligence", ["@root/design-intelligence/dependency-sources.yaml", "@root/tooling/experience/dependency_intelligence.py"]),
    (30, "Dependency refresh", ["@root/.github/workflows/design-connector-refresh.yml"]),
    (31, "UX telemetry", ["experience/design/learning-ledger.yaml", "@root/design-intelligence/ux-telemetry-policy.yaml"]),
    (32, "Human design feedback", ["experience/design/learning-ledger.yaml", "feedback/REV-BLD-reference-retail-a-ref001-approved.yaml"]),
    (33, "Learning loop", ["experience/design/learning-run.yaml", "@root/tooling/experience/learning_orchestrator.py"]),
    (34, "Component lifecycle", ["@root/design-intelligence/component-registry.yaml", "@root/tooling/experience/component_registry.py"]),
    (35, "Promotion gate", ["@root/tooling/experience/promotion_gate.py"]),
    (36, "Design debt", ["@root/design-intelligence/design-debt-baseline.yaml", "@root/tooling/experience/debt_gate.py"]),
    (37, "Flutter and web behavioral parity", ["@root/design-intelligence/behavior-contracts.yaml", "@root/tooling/experience/web_behavior.mjs", "@root/packages/agency_flutter_ui/test/behavior_parity_test.dart"]),
    (38, "Prototype creation and coverage", ["experience/prototypes/a-manifest.yaml", "experience/prototypes/a-coverage.yaml", "experience/prototypes/a-implementation.yaml"]),
    (39, "Visual and business review", ["experience/design/review-evidence-binding.yaml", "experience/visual-qa/VQA-BLD-reference-retail-a-ref001.yaml", "feedback/REV-BLD-reference-retail-a-ref001-approved.yaml"]),
    (40, "Immutable scope freeze", ["approved/current-scope.yaml", "approved/scope-baselines/BASE-reference-retail-v1.yaml"]),
]

def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected mapping in {path}")
    return value

def _resolve(project: Path, ref: str, root: Path) -> Path:
    return root / ref.removeprefix("@root/") if ref.startswith("@root/") else project / ref

def _required_files(project: Path, root: Path) -> list[str]:
    blockers: list[str] = []
    for point, _, refs in POINTS:
        for ref in refs:
            if not _resolve(project, ref, root).exists():
                blockers.append(f"point-{point}:missing:{ref}")
    return blockers

def _validate_review_binding(project: Path, root: Path) -> list[str]:
    blockers: list[str] = []
    binding_path = project / "experience/design/review-evidence-binding.yaml"
    errors = validate(binding_path, "review-evidence-binding")
    blockers.extend("review-binding:" + e for e in errors)
    if errors:
        return blockers
    binding = _load(binding_path)
    review = _load(project / binding["review_ref"])
    if review.get("status") != "approved":
        blockers.append("review-binding:review-not-approved")
    if review.get("build_id") != binding.get("build_id"):
        blockers.append("review-binding:build-mismatch")
    if review.get("direction_id") != binding.get("direction_id"):
        blockers.append("review-binding:direction-mismatch")
    for ref in binding.get("visual_qa_refs", []):
        qa = _load(project / ref)
        if qa.get("status") != "passed":
            blockers.append(f"review-binding:qa-not-passed:{ref}")
        if qa.get("build_identity") != binding.get("build_id"):
            blockers.append(f"review-binding:qa-build-mismatch:{ref}")
        if qa.get("direction_id") != binding.get("direction_id"):
            blockers.append(f"review-binding:qa-direction-mismatch:{ref}")
    baseline = _load(root / binding["approved_visual_baseline_ref"])
    if baseline.get("mode") != binding.get("baseline_mode"):
        blockers.append("review-binding:baseline-mode-mismatch")
    if len(baseline.get("captures", {})) != int(binding.get("baseline_patterns", 0)):
        blockers.append("review-binding:baseline-pattern-count-mismatch")
    expected_views = set(binding.get("baseline_viewports", []))
    for pattern, views in baseline.get("captures", {}).items():
        if set(views) != expected_views:
            blockers.append(f"review-binding:viewport-set-mismatch:{pattern}")
    return blockers

def _validate_scope(project: Path) -> tuple[list[str], dict[str, str]]:
    blockers: list[str] = []
    current_path = project / "approved/current-scope.yaml"
    current_errors = validate(current_path, "current-scope")
    blockers.extend("current-scope:" + e for e in current_errors)
    current = _load(current_path)
    baseline_path = project / current["baseline_ref"]
    baseline_errors = validate(baseline_path, "scope-baseline")
    blockers.extend("scope-baseline:" + e for e in baseline_errors)
    baseline = _load(baseline_path)
    if baseline.get("baseline_id") != current.get("baseline_id"):
        blockers.append("scope:baseline-id-mismatch")
    if baseline.get("immutable") is not True:
        blockers.append("scope:baseline-not-immutable")
    if baseline.get("review_ref") != "feedback/REV-BLD-reference-retail-a-ref001-approved.yaml":
        blockers.append("scope:approved-review-not-bound")
    return blockers, {
        "current_scope_ref": "approved/current-scope.yaml",
        "baseline_ref": current["baseline_ref"],
        "baseline_id": current["baseline_id"],
    }

def build_manifest(client: str, root: Path = ROOT) -> dict[str, Any]:
    project = root / "client-projects" / client
    blockers = _required_files(project, root)

    abc = audit_client(client, root, "a.yaml")
    if not abc["ready_for_client_review"]:
        for phase, data in abc["phases"].items():
            blockers.extend(f"abc-{phase}:{item}" for item in data["blockers"])

    pre = preprototype_evaluate(client, root)
    blockers.extend("preprototype:" + item for item in pre.get("blocking_items", []))

    try:
        assert_client_review_ready(client, "a.yaml", root)
    except Exception as exc:
        blockers.append("prototype-coverage:" + str(exc))

    learning = learning_drift(client, root)
    if learning.get("status") != "passed":
        blockers.append("learning-run:drift")

    debt = evaluate_debt(root)
    if debt.get("status") != "passed":
        blockers.extend("design-debt:" + str(x) for x in debt.get("new_findings", []))

    blockers.extend(_validate_review_binding(project, root))
    scope_blockers, scope = _validate_scope(project)
    blockers.extend(scope_blockers)

    # Contract authorities introduced specifically to close pre-production governance.
    contract_checks = [
        ("design-contract", project / "contracts/design-contract.yaml"),
        ("integration-contract", project / "contracts/integration-contract.yaml"),
        ("component-selection-ledger", project / "experience/design/selection-ledger.yaml"),
        ("design-connector-evidence", project / "experience/design/connector-evidence.yaml"),
        ("design-learning-ledger", project / "experience/design/learning-ledger.yaml"),
    ]
    for contract_type, path in contract_checks:
        for error in validate(path, contract_type):
            blockers.append(f"{contract_type}:{error}")

    unique_blockers = list(dict.fromkeys(blockers))
    points = [
        {"point": point, "name": name, "status": "pass", "evidence": refs}
        for point, name, refs in POINTS
    ] if not unique_blockers else []

    authorities = {
        "client_input": "input/client-input.yaml",
        "truth_register": "derived/truth-register.yaml",
        "classification": "derived/classification-evidence.yaml",
        "benchmark": "derived/benchmark-report.yaml",
        "capability_map": "derived/capability-map.yaml",
        "journey_map": "derived/journey-map.yaml",
        "entity_map": "derived/entity-map.yaml",
        "surface_map": "derived/surface-map.yaml",
        "integration_map": "derived/integration-map.yaml",
        "dependency_map": "derived/dependency-map.yaml",
        "solution_contract": "solution/solution-contract.yaml",
        "design_contract": "contracts/design-contract.yaml",
        "integration_contract": "contracts/integration-contract.yaml",
        "design_selection": "experience/design/selection.yaml",
        "selection_ledger": "experience/design/selection-ledger.yaml",
        "learning_run": "experience/design/learning-run.yaml",
        "direction": "experience/directions/a.yaml",
        "prototype_coverage": "experience/prototypes/a-coverage.yaml",
        "build_identity": "experience/builds/BLD-reference-retail-a-ref001.yaml",
        "review_binding": "experience/design/review-evidence-binding.yaml",
        "approved_review": "feedback/REV-BLD-reference-retail-a-ref001-approved.yaml",
        "scope_baseline": scope.get("baseline_ref", ""),
    }

    manifest = {
        "version": 1,
        "client_id": client,
        "status": "complete" if not unique_blockers else "blocked",
        "scope": scope,
        "authorities": authorities,
        "points": points,
        "visual_evidence": {
            "baseline_ref": "design-intelligence/approved-visual-baselines.yaml",
            "baseline_mode": "exact-png-hash",
            "review_binding_ref": "experience/design/review-evidence-binding.yaml",
        },
        "immutable": True,
    }
    if unique_blockers:
        manifest["blocking_items"] = unique_blockers
    return manifest

def assert_drift_free(client: str, root: Path = ROOT) -> dict[str, Any]:
    actual = build_manifest(client, root)
    expected_path = root / "client-projects" / client / "approved/preproduction-completion.yaml"
    expected = _load(expected_path)
    return {
        "status": "passed" if actual == expected else "blocked",
        "actual": actual,
        "expected": expected,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Verify PinCommerce points 1-40 pre-production completion")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check-drift", action="store_true")
    args = parser.parse_args()
    result = assert_drift_free(args.client, args.root) if args.check_drift else build_manifest(args.client, args.root)
    print(yaml.safe_dump(result, sort_keys=False))
    if args.check_drift:
        return 0 if result["status"] == "passed" else 2
    return 0 if result["status"] == "complete" else 2

if __name__ == "__main__":
    raise SystemExit(main())
