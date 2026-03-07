import type { Meta, StoryObj } from '@storybook/vue3';
import { Progress } from './index';

const meta: Meta<typeof Progress> = {
  title: 'UI/Progress',
  component: Progress,
  tags: ['autodocs'],
  argTypes: {
    modelValue: { control: { type: 'range', min: 0, max: 100 } },
  },
};

export default meta;
type Story = StoryObj<typeof Progress>;

export const Default: Story = {
  args: {
    modelValue: 45,
  },
};

export const Full: Story = {
  args: {
    modelValue: 100,
  },
};
