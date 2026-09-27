// Representative demo data for the consolidated commerce+ERP admin (design
// phase). INR amounts mirror the reference retail baseline. In production this
// is fed by Medusa (commerce) + Tryton (ERP) via the governed adapters.
export type ProductRow = {
  id: string;
  name: string;
  sku: string;
  price: string;
  stock: number;
  status: "in-stock" | "low-stock" | "out-of-stock";
};

export type OrderRow = {
  id: string;
  customer: string;
  type: "B2B" | "D2C";
  total: string;
  status: "pending" | "paid" | "fulfilled" | "returned";
};

export type SalesOrderRow = {
  id: string;
  customer: string;
  amount: string;
  status: "draft" | "confirmed" | "invoiced" | "closed";
  erp: string;
};

export type InventoryRow = {
  sku: string;
  name: string;
  onHand: number;
  reserved: number;
  available: number;
  warehouse: string;
};

export type ExceptionRow = { id: string; summary: string; status: string };

export const kpis = [
  { label: "Gross revenue (30d)", value: "₹48.2L", trendLabel: "+12% vs prior" },
  { label: "Orders (30d)", value: "1,284", trendLabel: "+8% vs prior" },
  { label: "Open sales orders", value: "37", trendLabel: "ERP sync current" },
  { label: "Inventory value", value: "₹1.9Cr", trendLabel: "12 SKUs low stock" },
];

export const products: ProductRow[] = [
  { id: "prod_001", name: "Wireless Headphones", sku: "SKU-1001", price: "₹1,999", stock: 142, status: "in-stock" },
  { id: "prod_002", name: "Leather Sneakers", sku: "SKU-1002", price: "₹3,499", stock: 8, status: "low-stock" },
  { id: "prod_003", name: "Cotton T-Shirt", sku: "SKU-1003", price: "₹499", stock: 0, status: "out-of-stock" },
  { id: "prod_004", name: "Smart Watch", sku: "SKU-1004", price: "₹2,499", stock: 64, status: "in-stock" },
  { id: "prod_005", name: "Travel Backpack", sku: "SKU-1005", price: "₹1,299", stock: 31, status: "in-stock" },
  { id: "prod_006", name: "Desk Lamp", sku: "SKU-1006", price: "₹899", stock: 5, status: "low-stock" },
];

export const orders: OrderRow[] = [
  { id: "ORD-1001", customer: "CUST-B2B-014", type: "B2B", total: "₹1,85,000", status: "paid" },
  { id: "ORD-1002", customer: "CUST-D2C-207", type: "D2C", total: "₹3,998", status: "fulfilled" },
  { id: "ORD-1003", customer: "CUST-B2B-021", type: "B2B", total: "₹92,400", status: "pending" },
  { id: "ORD-1004", customer: "CUST-D2C-311", type: "D2C", total: "₹2,499", status: "returned" },
  { id: "ORD-1005", customer: "CUST-B2B-014", type: "B2B", total: "₹1,28,700", status: "pending" },
];

export const salesOrders: SalesOrderRow[] = [
  { id: "SO-2001", customer: "CUST-B2B-014", amount: "₹1,85,000", status: "invoiced", erp: "tryton" },
  { id: "SO-2002", customer: "CUST-B2B-021", amount: "₹92,400", status: "confirmed", erp: "tryton" },
  { id: "SO-2003", customer: "CUST-B2B-033", amount: "₹44,150", status: "draft", erp: "tryton" },
  { id: "SO-2004", customer: "CUST-B2B-014", amount: "₹1,28,700", status: "confirmed", erp: "tryton" },
  { id: "SO-2005", customer: "CUST-B2B-045", amount: "₹61,250", status: "closed", erp: "tryton" },
];

export const inventory: InventoryRow[] = [
  { sku: "SKU-1001", name: "Wireless Headphones", onHand: 160, reserved: 18, available: 142, warehouse: "BLR-01" },
  { sku: "SKU-1002", name: "Leather Sneakers", onHand: 14, reserved: 6, available: 8, warehouse: "BLR-01" },
  { sku: "SKU-1003", name: "Cotton T-Shirt", onHand: 0, reserved: 0, available: 0, warehouse: "BLR-01" },
  { sku: "SKU-1004", name: "Smart Watch", onHand: 70, reserved: 6, available: 64, warehouse: "DEL-02" },
  { sku: "SKU-1005", name: "Travel Backpack", onHand: 40, reserved: 9, available: 31, warehouse: "DEL-02" },
];

export const exceptions: ExceptionRow[] = [
  { id: "DLQ-001", summary: "erp.create_sales_order failed — Tryton connection refused", status: "retrying" },
  { id: "REC-014", summary: "commerce-order-to-erp amount mismatch (₹1,200)", status: "open" },
  { id: "DLQ-002", summary: "payments.capture duplicate for ORD-1003", status: "open" },
  { id: "REC-009", summary: "inventory reservation drift — SKU-1002", status: "resolved" },
];
