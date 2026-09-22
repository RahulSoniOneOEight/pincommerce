from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


class SeedBundleError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SeedBundleError(f"Missing demo dataset: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SeedBundleError(f"Expected mapping in {path}")
    return value


def build_seed_bundle(dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    masters = dataset.get("masters", {})
    tx = dataset.get("transactions", {})
    finance = dataset.get("finance", {})

    medusa = {
        "provider": "medusa",
        "source_dataset": dataset["dataset_id"],
        "customers": masters.get("customers", []),
        "products": masters.get("products", []),
        "warehouses": masters.get("warehouses", []),
        "inventory": tx.get("inventory", []),
        "orders": tx.get("orders", []),
        "payments": tx.get("payments", []),
        "shipments": tx.get("shipments", []),
        "returns": tx.get("returns", []),
    }
    mercur = {
        "provider": "mercur",
        "source_dataset": dataset["dataset_id"],
        "sellers": masters.get("sellers", []),
        "seller_settlements": tx.get("seller_settlements", []),
        "orders": [o for o in tx.get("orders", []) if o.get("seller_id")],
    }
    tryton = {
        "provider": "tryton",
        "source_dataset": dataset["dataset_id"],
        "parties": masters.get("customers", []) + masters.get("suppliers", []),
        "products": masters.get("products", []),
        "warehouses": masters.get("warehouses", []),
        "stock": tx.get("inventory", []),
        "sales_orders": tx.get("orders", []),
        "purchase_orders": tx.get("purchases", []),
        "customer_invoices": finance.get("invoices", []),
        "receivables": finance.get("receivables", []),
        "payables": finance.get("payables", []),
        "journal_entries": finance.get("journal_entries", []),
        "reconciliations": finance.get("reconciliations", []),
    }
    return {"medusa": medusa, "mercur": mercur, "tryton": tryton}


def write_seed_bundle(client_id: str, root: Path = ROOT, overwrite: bool = False) -> list[Path]:
    project = root / "client-projects" / client_id
    dataset_path = project / "experience" / "fixtures" / f"{client_id}-demo-dataset.yaml"
    dataset = load_yaml(dataset_path)
    outputs = build_seed_bundle(dataset)
    seed_dir = project / "experience" / "fixtures" / "provider-seeds"
    seed_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for provider, value in outputs.items():
        path = seed_dir / f"{provider}.yaml"
        if path.exists() and not overwrite:
            raise SeedBundleError(f"Refusing to overwrite: {path}")
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate provider-specific prototype seed bundles")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        for path in write_seed_bundle(args.client, args.root, args.overwrite):
            print(path.relative_to(args.root))
        return 0
    except SeedBundleError as exc:
        print(f"seed-bundle-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
