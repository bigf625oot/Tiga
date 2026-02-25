import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import TaskNode from '../TaskNode.vue';

// Mock Vue Flow components as they might need context
vi.mock('@vue-flow/core', () => ({
  Handle: {
    template: '<div class="handle"></div>',
    props: ['type', 'position']
  }
}));

// Mock Icons
vi.mock('@ant-design/icons-vue', () => ({
  CheckCircleOutlined: { template: '<span class="icon-check"></span>' },
  SyncOutlined: { template: '<span class="icon-sync"></span>' },
  ClockCircleOutlined: { template: '<span class="icon-clock"></span>' },
  CloseCircleOutlined: { template: '<span class="icon-close"></span>' }
}));

describe('TaskNode.vue', () => {
  it('renders correctly with pending status', () => {
    const wrapper = mount(TaskNode, {
      props: {
        data: {
          label: 'Test Task',
          status: 'pending'
        }
      }
    });

    expect(wrapper.text()).toContain('Test Task');
    expect(wrapper.text()).toContain('pending');
    expect(wrapper.find('.bg-slate-200').exists()).toBe(true); // Default icon bg
  });

  it('renders correctly with running status', () => {
    const wrapper = mount(TaskNode, {
      props: {
        data: {
          label: 'Running Task',
          status: 'running',
          progress: 50
        }
      }
    });

    expect(wrapper.text()).toContain('Running Task');
    expect(wrapper.classes()).toContain('border-blue-500');
    expect(wrapper.find('.bg-blue-500').exists()).toBe(true);
    // Check progress bar
    const progressBar = wrapper.find('.bg-blue-500.animate-pulse');
    expect(progressBar.exists()).toBe(true);
    expect(progressBar.attributes('style')).toContain('width: 50%');
  });

  it('renders correctly with completed status', () => {
    const wrapper = mount(TaskNode, {
      props: {
        data: {
          label: 'Done Task',
          status: 'completed'
        }
      }
    });

    expect(wrapper.classes()).toContain('border-green-500');
    expect(wrapper.find('.icon-check').exists()).toBe(true);
  });

  it('renders correctly with failed status', () => {
    const wrapper = mount(TaskNode, {
      props: {
        data: {
          label: 'Failed Task',
          status: 'failed'
        }
      }
    });

    expect(wrapper.classes()).toContain('border-red-500');
    expect(wrapper.find('.icon-close').exists()).toBe(true);
  });
});
