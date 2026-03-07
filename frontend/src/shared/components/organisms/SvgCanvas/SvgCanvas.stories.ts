import type { Meta, StoryObj } from '@storybook/vue3';
import SvgCanvas from './SvgCanvas.vue';
import { ref } from 'vue';

const meta: Meta<typeof SvgCanvas> = {
  title: 'Shared/Organisms/SvgCanvas',
  component: SvgCanvas,
  tags: ['autodocs'],
  argTypes: {
    width: { control: 'number' },
    height: { control: 'number' },
    isLightMode: { control: 'boolean' },
    onBoundaryClamp: { action: 'boundaryClamp' },
    'onUpdate:nodes': { action: 'update:nodes' },
  },
};

export default meta;
type Story = StoryObj<typeof SvgCanvas>;

export const LightModeWithClamping: Story = {
  render: (args) => ({
    components: { SvgCanvas },
    setup() {
      const nodes = ref([
        { id: '1', x: 50, y: 50, width: 100, height: 60, label: 'Drag Me', color: '#3b82f6' },
        { id: '2', x: 300, y: 150, width: 120, height: 80, label: 'Boundary Test', color: '#10b981' },
      ]);
      return { args, nodes };
    },
    template: `
      <div class="p-4 bg-slate-100 dark:bg-slate-900">
        <h3 class="mb-2 text-sm font-semibold">SVG Canvas (800x600)</h3>
        <SvgCanvas 
            v-bind="args" 
            v-model:nodes="nodes" 
        />
      </div>
    `,
  }),
  args: {
    width: 800,
    height: 600,
    isLightMode: true,
  },
};
