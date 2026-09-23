import type { Meta, StoryObj } from "@storybook/react";
import { CategoryRail } from "@pincommerce/agency-web-ui";
const meta = { title: "Commerce/CategoryRail", component: CategoryRail, args: { categories: ["New", "Beauty", "Wellness", "Home"] } } satisfies Meta<typeof CategoryRail>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {};
export const Empty: Story = { args: { categories: [], state: "empty" } };
export const Loading: Story = { args: { state: "loading" } };
