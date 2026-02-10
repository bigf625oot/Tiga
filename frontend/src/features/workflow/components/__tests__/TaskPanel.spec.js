/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import TaskPanel from '../TaskPanel.vue';

// Mock the store
vi.mock('../../store/workflow.store', () => ({
    useWorkflowStore: () => ({
        progress: 50,
        tasks: [],
        logs: [],
        isRunning: true,
        currentStep: 'Step 1',
        stopWorkflow: vi.fn(),
        clearLogs: vi.fn()
    })
}));

describe('TaskPanel.vue', () => {
  it('renders correctly', () => {
    const wrapper = mount(TaskPanel, {
      global: {
        stubs: {
          'TaskTree': true,
          'LogDrawer': true,
          'AppstoreOutlined': true,
          'StopOutlined': true,
          'CodeOutlined': true
        }
      }
    });

    expect(wrapper.text()).toContain('任务执行');
    expect(wrapper.text()).toContain('50%');
    expect(wrapper.text()).toContain('执行中');
    expect(wrapper.text()).toContain('Step 1');
  });

  it('opens log drawer on click', async () => {
    const wrapper = mount(TaskPanel, {
      global: {
        stubs: {
          'TaskTree': true,
          'LogDrawer': true,
          'AppstoreOutlined': true,
          'StopOutlined': true,
          'CodeOutlined': true
        }
      }
    });

    // Find the footer div that contains "系统日志"
    const footer = wrapper.find('.border-t');
    await footer.find('div').trigger('click');

    expect(wrapper.vm.logDrawerVisible).toBe(true);
  });
});
