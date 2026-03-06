import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import TaskGraph from '../TaskGraph.vue';
import { createPinia, setActivePinia } from 'pinia';

// Mock Vue Flow
vi.mock('@vue-flow/core', () => ({
  VueFlow: { template: '<div><slot /></div>' },
  useVueFlow: () => ({ fitView: vi.fn() }),
  Handle: { template: '<div></div>' }
}));

vi.mock('@vue-flow/background', () => ({
  Background: { template: '<div></div>' }
}));

vi.mock('@vue-flow/controls', () => ({
  Controls: { template: '<div></div>' }
}));

vi.mock('@vue-flow/minimap', () => ({
  MiniMap: { template: '<div></div>' }
}));

describe('TaskGraph.vue', () => {
  it('renders without crashing', () => {
    setActivePinia(createPinia());
    const wrapper = mount(TaskGraph);
    expect(wrapper.exists()).toBe(true);
  });
});
