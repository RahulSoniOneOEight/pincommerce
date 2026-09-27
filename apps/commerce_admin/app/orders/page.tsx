import { Surface } from "@pincommerce/agency-web-ui";
import { DataTable, Status } from "../components";
import { orders } from "../../lib/demo-data";

export default function OrdersPage() {
  return (
    <Surface>
      <header className="page-header">
        <p className="eyebrow">Commerce</p>
        <h1>Orders</h1>
      </header>
      <DataTable
        caption="Orders (Medusa)"
        columns={["Order", "Customer", "Type", "Total", "Status"]}
        rows={orders.map((o) => [
          o.id,
          o.customer,
          o.type,
          o.total,
          <Status key="s" value={o.status} />,
        ])}
      />
    </Surface>
  );
}
