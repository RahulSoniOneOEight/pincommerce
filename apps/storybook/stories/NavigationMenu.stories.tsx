import type { Meta, StoryObj } from "@storybook/react";
import { NavigationMenu } from "@pincommerce/agency-web-ui";
const meta = { title: "Commerce/NavigationMenu", component: NavigationMenu, args: { items: ["Home", "Catalog", "Orders", "Account"], current: "Catalog" } } satisfies Meta<typeof NavigationMenu>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {};
export const Disabled: Story = { args: { state: "disabled" } };
