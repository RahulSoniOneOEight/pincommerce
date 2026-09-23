import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { B2BQuickOrder, FilterBar, FormSection, NavigationMenu } from "@pincommerce/agency-web-ui";

function BehaviorParityProbe() {
  const [filter, setFilter] = useState("none");
  const [lines, setLines] = useState([{ sku: "SKU-1", name: "Reference Product", quantity: 1 }]);
  const [current, setCurrent] = useState("Home");
  const [value, setValue] = useState("a");

  return <div>
    <FilterBar filters={["In stock"]} onSelect={setFilter} />
    <output data-testid="filter-output">{filter}</output>

    <B2BQuickOrder lines={lines} onQuantityChange={(sku, quantity) => setLines([{ sku, name: "Reference Product", quantity }])} />
    <output data-testid="quantity-output">{lines[0].quantity}</output>

    <NavigationMenu items={["Home", "Catalog"]} current={current} onNavigate={setCurrent} />
    <output data-testid="navigation-output">{current}</output>

    <FormSection label="Name" value={value} onChange={setValue} />
    <output data-testid="form-output">{value}</output>
  </div>;
}

const meta = { title: "Governance/BehaviorParity", component: BehaviorParityProbe } satisfies Meta<typeof BehaviorParityProbe>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {};
