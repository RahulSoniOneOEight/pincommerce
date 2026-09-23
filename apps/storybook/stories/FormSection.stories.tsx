import type { Meta, StoryObj } from "@storybook/react";
import { FormSection } from "@pincommerce/agency-web-ui";
const meta = { title: "Commerce/FormSection", component: FormSection, args: { label: "Email", value: "buyer@example.com", helper: "Order updates are sent here" } } satisfies Meta<typeof FormSection>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Default: Story = {};
export const ValidationError: Story = { args: { state: "validation-error", error: "Enter a valid email" } };
export const Disabled: Story = { args: { state: "disabled" } };
