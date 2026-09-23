import type { Meta, StoryObj } from "@storybook/react";
import { FilterBar } from "@pincommerce/agency-web-ui";
const meta = { title: "Commerce/FilterBar", component: FilterBar, args: { filters: ["In stock", "Fast delivery", "Under ₹2,000"], selected: ["In stock"] } } satisfies Meta<typeof FilterBar>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {};
export const Disabled: Story = { args: { state: "disabled" } };
