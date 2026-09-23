import type { Meta, StoryObj } from "@storybook/react";
import { CheckoutSummary } from "@pincommerce/agency-web-ui";
const meta = { title: "Commerce/CheckoutSummary", component: CheckoutSummary, args: { subtotal: "₹2,499", shipping: "₹99", total: "₹2,598" } } satisfies Meta<typeof CheckoutSummary>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {};
export const Loading: Story = { args: { state: "loading" } };
export const Disabled: Story = { args: { state: "disabled" } };
