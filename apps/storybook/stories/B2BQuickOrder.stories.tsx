import type { Meta, StoryObj } from "@storybook/react";
import { B2BQuickOrder } from "@pincommerce/agency-web-ui";
const meta = { title: "Commerce/B2BQuickOrder", component: B2BQuickOrder, args: { lines: [{ sku: "SKU-001", name: "Reference Product", quantity: 12 }, { sku: "SKU-002", name: "Second Product", quantity: 6 }] } } satisfies Meta<typeof B2BQuickOrder>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {};
export const Empty: Story = { args: { lines: [], state: "empty" } };
export const Loading: Story = { args: { state: "loading" } };
