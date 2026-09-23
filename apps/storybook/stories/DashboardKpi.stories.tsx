import type { Meta, StoryObj } from "@storybook/react";
import { DashboardKpi } from "@pincommerce/agency-web-ui";
const meta = { title: "Commerce/DashboardKpi", component: DashboardKpi, args: { label: "Net sales", value: "₹12.4L", trendLabel: "+8.2% vs prior period" } } satisfies Meta<typeof DashboardKpi>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {};
export const Loading: Story = { args: { state: "loading" } };
export const Failure: Story = { args: { state: "failure" } };
