import type { Meta, StoryObj } from "@storybook/react";
import { ExceptionTable } from "@pincommerce/agency-web-ui";
const meta = { title: "Commerce/ExceptionTable", component: ExceptionTable, args: { items: [{ id: "EX-101", summary: "Settlement mismatch", status: "Open" }, { id: "EX-102", summary: "Inventory variance", status: "Review" }] } } satisfies Meta<typeof ExceptionTable>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {};
export const Empty: Story = { args: { items: [], state: "empty" } };
export const Loading: Story = { args: { state: "loading" } };
