/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import TaskPanel from '../TaskPanel.vue';
import LogDrawer from '../drawer/LogDrawer.vue';

// Mock the store
vi.mock('../../store/workflow.store', () => ({
    useWorkflowStore: () => ({
        progress: 50,
        tasks: [
            { name: 'Task 1', logs: [] },
            { name: 'Task 2', logs: [] }
        ],
        logs: [],
        isRunning: true,
        currentStep: 'Step 1',
        stopWorkflow: vi.fn(),
        clearLogs: vi.fn()
    })
}));

// Mock i18n
vi.mock('../../../../locales', () => ({
  useI18n: () => ({
    t: (key) => key
  })
}));

describe('TaskPanel.vue', () => {
  const stubs = {
    'TaskTree': true,
    'LogDrawer': true,
    'AgentStatusDashboard': { template: '<div>Dashboard</div>' }, // Stub dashboard
    'TaskGraph': true, // Stub graph
    'ArtifactEditor': true,
    'SandboxResultViewer': true,
    'SandboxTerminal': true,
    'EmptyState': true,
    'a-segmented': { template: '<div><slot name="label" :payload="{labelKey: \'taskView\'}"></slot></div>' }, // Minimal stub
    'a-slider': true,
    'AppstoreOutlined': true,
    'StopOutlined': true,
    'CodeOutlined': true,
    'ApartmentOutlined': true,
    'PlayCircleOutlined': true,
    'LeftOutlined': true,
    'RightOutlined': true,
    'FileTextOutlined': true
  };

  it('renders correctly', () => {
    const wrapper = mount(TaskPanel, {
      global: { stubs }
    });

    // Check for i18n key instead of text
    expect(wrapper.text()).toContain('taskView'); 
    
    // Check if tasks are rendered (since activeView defaults to 'tasks')
    expect(wrapper.text()).toContain('Task 1');
    expect(wrapper.text()).toContain('Task 2');
  });

  it('opens log drawer on click', async () => {
    const wrapper = mount(TaskPanel, {
      global: { stubs }
    });

    // Find the log trigger button
    const logBtn = wrapper.find('.log-trigger');
    expect(logBtn.exists()).toBe(true);
    
    await logBtn.trigger('click');

    // Check if LogDrawer prop visible became true
    const drawer = wrapper.findComponent(LogDrawer);
    expect(drawer.exists()).toBe(true);
    expect(drawer.props('visible')).toBe(true);
  });
});
