from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from tooling.contracts.validator import validate_document

ROOT = Path(__file__).resolve().parents[2]


class DemoDataError(RuntimeError):
    pass


def build_demo_dataset(client_id: str) -> dict[str, Any]:
    dataset = {
        "dataset_id": f"DEMO-{client_id}-v1",
        "client_id": client_id,
        "profile": "realistic-retail",
        "masters": {
            "customers": [
                {"id": "CUST-B2C-001", "name": "Aarav Demo", "type": "b2c"},
                {
                    "id": "CUST-B2B-014",
                    "name": "Metro Hardware Demo",
                    "type": "b2b",
                    "gstin": "29ABCDE1234F1Z5",
                    "credit_limit": 500000,
                    "credit_available": 185000,
                },
            ],
            "products": [
                {"id": "SKU-1001", "name": "Reference Product A", "mrp": 1999, "gst_rate": 18, "uom": "each"},
                {"id": "SKU-2001", "name": "Reference Product B", "mrp": 4800, "gst_rate": 18, "uom": "case"},
            ],
            "warehouses": [
                {"id": "BLR-01", "name": "Bengaluru Central"},
                {"id": "BLR-02", "name": "Bengaluru North"},
            ],
            "suppliers": [{"id": "SUP-001", "name": "Demo Supplies Pvt Ltd"}],
            "sellers": [
                {"id": "SELLER-001", "name": "Demo Seller One", "status": "active", "commission_percent": 10},
                {"id": "SELLER-002", "name": "Demo Seller Two", "status": "pending", "commission_percent": 8},
            ],
        },
        "transactions": {
            "orders": [
                {"id": "ORD-1001", "customer_id": "CUST-B2C-001", "status": "delivered", "total": 11800, "payment_status": "captured", "shipment_status": "delivered"},
                {"id": "ORD-1002", "customer_id": "CUST-B2C-001", "status": "payment_failed", "total": 4720, "payment_status": "failed", "shipment_status": "not_created"},
                {"id": "ORD-1003", "customer_id": "CUST-B2B-014", "status": "approval_pending", "total": 124800, "payment_status": "part_credit", "shipment_status": "pending"},
                {"id": "ORD-1004", "customer_id": "CUST-B2B-014", "status": "partially_fulfilled", "total": 86400, "payment_status": "captured", "shipment_status": "partial"},
                {"id": "ORD-1005", "customer_id": "CUST-B2C-001", "status": "return_requested", "total": 23600, "payment_status": "captured", "shipment_status": "delivered"},
                {"id": "ORD-1006", "customer_id": "CUST-B2C-001", "status": "refund_pending", "total": 5900, "payment_status": "refund_pending", "shipment_status": "returned"},
                {"id": "ORD-1007", "customer_id": "CUST-B2B-014", "status": "inventory_shortage", "total": 43200, "payment_status": "pending", "shipment_status": "blocked"},
                {"id": "ORD-1008", "customer_id": "CUST-B2C-001", "status": "reconciliation_mismatch", "total": 12980, "payment_status": "captured", "shipment_status": "shipped"},
                {"id": "ORD-1009", "customer_id": "CUST-B2B-014", "status": "delivered", "total": 100000, "payment_status": "credit", "shipment_status": "delivered"},
                {"id": "ORD-1010", "customer_id": "CUST-B2C-001", "status": "seller_settlement_pending", "total": 17500, "payment_status": "captured", "shipment_status": "delivered", "seller_id": "SELLER-001"},
            ],
            "payments": [
                {"id": "PAY-1001", "order_id": "ORD-1001", "provider": "razorpay-mock", "status": "captured", "amount": 11800},
                {"id": "PAY-1002", "order_id": "ORD-1002", "provider": "razorpay-mock", "status": "failed", "amount": 4720},
                {"id": "PAY-1003A", "order_id": "ORD-1003", "provider": "razorpay-mock", "status": "captured", "amount": 24800},
                {"id": "PAY-1003B", "order_id": "ORD-1003", "provider": "credit", "status": "approved", "amount": 100000},
            ],
            "shipments": [
                {"id": "SHP-1001", "order_id": "ORD-1001", "provider": "shiprocket-mock", "awb": "SRDEMO982173", "status": "delivered"},
                {"id": "SHP-1008", "order_id": "ORD-1008", "provider": "shiprocket-mock", "awb": "SRDEMO982181", "status": "in_transit"},
            ],
            "returns": [
                {"id": "RET-1005", "order_id": "ORD-1005", "status": "qc_pending", "refund_status": "not_started"},
                {"id": "RET-1006", "order_id": "ORD-1006", "status": "received", "refund_status": "pending"},
            ],
            "inventory": [
                {"sku": "SKU-1001", "warehouse": "BLR-01", "on_hand": 42, "reserved": 7, "available": 35},
                {"sku": "SKU-2001", "warehouse": "BLR-01", "on_hand": 8, "reserved": 8, "available": 0},
                {"sku": "SKU-2001", "warehouse": "BLR-02", "on_hand": 17, "reserved": 2, "available": 15},
            ],
            "purchases": [
                {"id": "PO-3001", "supplier_id": "SUP-001", "status": "partially_received", "total": 250000},
                {"id": "PO-3002", "supplier_id": "SUP-001", "status": "approved", "total": 125000},
            ],
            "seller_settlements": [
                {"id": "SET-001", "seller_id": "SELLER-001", "gross": 17500, "commission": 1750, "payable": 15750, "status": "pending"}
            ],
        },
        "finance": {
            "invoices": [
                {"id": "INV-1001", "order_id": "ORD-1001", "taxable": 10000, "gst": 1800, "gross": 11800, "status": "paid"},
                {"id": "INV-1009", "order_id": "ORD-1009", "taxable": 84745.76, "gst": 15254.24, "gross": 100000, "status": "partially_paid", "outstanding": 50000},
            ],
            "receivables": [
                {"customer_id": "CUST-B2B-014", "invoice_id": "INV-1009", "amount": 100000, "collected": 50000, "outstanding": 50000, "age_days": 21}
            ],
            "payables": [
                {"supplier_id": "SUP-001", "purchase_id": "PO-3001", "amount": 250000, "paid": 100000, "outstanding": 150000}
            ],
            "journal_entries": [
                {
                    "id": "JE-INV-1001",
                    "source": "INV-1001",
                    "lines": [
                        {"account": "Accounts Receivable", "debit": 11800, "credit": 0},
                        {"account": "Sales Revenue", "debit": 0, "credit": 10000},
                        {"account": "Output GST", "debit": 0, "credit": 1800}
                    ]
                },
                {
                    "id": "JE-PAY-1001",
                    "source": "PAY-1001",
                    "lines": [
                        {"account": "Bank", "debit": 11800, "credit": 0},
                        {"account": "Accounts Receivable", "debit": 0, "credit": 11800}
                    ]
                },
                {
                    "id": "JE-COGS-1001",
                    "source": "ORD-1001",
                    "lines": [
                        {"account": "COGS", "debit": 6200, "credit": 0},
                        {"account": "Inventory", "debit": 0, "credit": 6200}
                    ]
                }
            ],
            "reconciliations": [
                {"id": "REC-1001", "order_id": "ORD-1001", "status": "matched"},
                {"id": "REC-1008", "order_id": "ORD-1008", "status": "mismatch", "difference": 180}
            ]
        },
        "scenario_coverage": [
            "successful-order",
            "payment-failed",
            "approval-pending",
            "partial-shipment",
            "return-requested",
            "refund-pending",
            "inventory-shortage",
            "reconciliation-mismatch",
            "overdue-receivable",
            "seller-settlement-pending"
        ],
        "status": "ready",
    }
    errors = validate_document(dataset, "prototype-demo-dataset")
    if errors:
        raise DemoDataError("Generated demo dataset invalid: " + "; ".join(errors))
    return dataset


def write_demo_dataset(client_id: str, root: Path = ROOT, overwrite: bool = False) -> Path:
    path = root / "client-projects" / client_id / "experience" / "fixtures" / f"{client_id}-demo-dataset.yaml"
    if path.exists() and not overwrite:
        raise DemoDataError(f"Refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(build_demo_dataset(client_id), sort_keys=False), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic commerce/ERP prototype demo data")
    parser.add_argument("--client", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        path = write_demo_dataset(args.client, args.root, args.overwrite)
        print(path.relative_to(args.root))
        return 0
    except DemoDataError as exc:
        print(f"demo-data-error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
