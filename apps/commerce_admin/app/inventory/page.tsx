import { Surface } from "@pincommerce/agency-web-ui";
import { DataTable, Status } from "../components";
import { inventory } from "../../lib/demo-data";

export default function InventoryPage() {
  return (
    <Surface>
      <header className="page-header">
        <p className="eyebrow">ERP</p>
        <h1>Inventory</h1>
      </header>
      <DataTable
        caption="Inventory (Tryton)"
        columns={["SKU", "Name", "On hand", "Reserved", "Available", "Warehouse"]}
        rows={inventory.map((i) => [
          i.sku,
          i.name,
          String(i.onHand),
          String(i.reserved),
          String(i.available),
          i.warehouse,
        ])}
      />
    </Surface>
  );
}
