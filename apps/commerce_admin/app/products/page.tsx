import { Surface } from "@pincommerce/agency-web-ui";
import { DataTable, Status } from "../components";
import { products } from "../../lib/demo-data";

export default function ProductsPage() {
  return (
    <Surface>
      <header className="page-header">
        <p className="eyebrow">Commerce</p>
        <h1>Products</h1>
      </header>
      <DataTable
        caption="Catalog (Medusa)"
        columns={["Name", "SKU", "Price", "Stock", "Status"]}
        rows={products.map((p) => [
          p.name,
          p.sku,
          p.price,
          String(p.stock),
          <Status key="s" value={p.status} />,
        ])}
      />
    </Surface>
  );
}
