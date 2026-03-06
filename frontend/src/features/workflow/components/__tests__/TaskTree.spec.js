/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect } from 'vitest';
import TaskTree from '../TaskTree.vue';

describe('TaskTree.vue', () => {
  const stubs = {
    ClockCircleOutlined: { template: '<span class="icon-clock" />' },
    LinkOutlined: { template: '<span class="icon-link" />' },
    CheckCircleOutlined: { template: '<span class="icon-check" />' },
    SyncOutlined: { template: '<span class="icon-sync" />' },
    CloseCircleOutlined: { template: '<span class="icon-close" />' }
  };

  it('renders running task with progress bar and status classes', () => {
    const tasks = [
      { id: 1, name: 'Run', status: 'running', description: 'desc', dependencies: [], estimatedTime: 5 }
    ];
    const wrapper = mount(TaskTree, { props: { tasks }, global: { stubs } });
    expect(wrapper.text()).toContain('Run');
    // status classes present
    expect(wrapper.find('.bg-blue-500').exists()).toBe(true);
    // progress bar exists
    expect(wrapper.find('.bg-blue-500.animate-pulse').exists()).toBe(true);
  });

  it('renders children recursively', () => {
    const tasks = [
      { id: 1, name: 'Parent', status: 'completed', children: [{ id: 2, name: 'Child', status: 'pending' }] }
    ];
    const wrapper = mount(TaskTree, { props: { tasks }, global: { stubs } });
    expect(wrapper.text()).toContain('Parent');
    expect(wrapper.text()).toContain('Child');
  });
});
