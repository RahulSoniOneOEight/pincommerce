import { Surface } from "@pincommerce/agency-web-ui";
import { DataTable, Status } from "../components";
import { salesOrders } from "../../lib/demo-data";

export default function SalesOrdersPage() {
  return (
    <Surface>
      <header className="page-header">
        <p className="eyebrow">ERP</p>
        <h1>Sales orders</h1>
        <p className="agency-muted">Synced to Tryton via erp.create_sales_order.</p>
      </header>
      <DataTable
        caption="Sales orders (Tryton)"
        columns={["SO", "Customer", "Amount", "Status", "ERP"]}
        rows={salesOrders.map((so) => [
          so.id,
          so.customer,
          so.amount,
          <Status key="s" value={so.status} />,
          so.erp,
        ])}
      />
    </Surface>
  );
}
