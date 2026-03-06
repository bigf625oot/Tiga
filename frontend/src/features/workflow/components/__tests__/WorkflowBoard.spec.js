/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import WorkflowBoard from '../WorkflowBoard.vue';

vi.mock('../../store/workflow.store', () => ({
  useWorkflowStore: () => ({
    progress: 75,
    currentStep: 'Plan',
    isRunning: true,
    tasks: [{ id: 't1', name: 'Task A', status: 'running' }],
    logs: [{ message: 'Start' }],
    stopWorkflow: vi.fn()
  })
}));

describe('WorkflowBoard.vue', () => {
  const stubs = {
    TaskTree: { template: '<div class="stub-task-tree"></div>' },
    LogPanel: { template: '<div class="stub-log-panel"></div>' }
  };

  it('renders header stats and controls', () => {
    const wrapper = mount(WorkflowBoard, { global: { stubs } });
    expect(wrapper.text()).toContain('任务进度');
    expect(wrapper.text()).toContain('当前步骤');
    expect(wrapper.text()).toContain('状态');
    expect(wrapper.text()).toContain('执行中...');
    // Progress bar width style reflects store.progress
    const bar = wrapper.find('div[style*="width:"]');
    expect(bar.attributes('style')).toContain('75%');
    // Stop button visible when running
    expect(wrapper.text()).toContain('停止执行');
  });

  it('renders TaskTree and LogPanel', () => {
    const wrapper = mount(WorkflowBoard, { global: { stubs } });
    expect(wrapper.find('.stub-task-tree').exists()).toBe(true);
    expect(wrapper.find('.stub-log-panel').exists()).toBe(true);
  });
});
