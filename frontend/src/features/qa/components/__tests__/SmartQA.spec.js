
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import SmartQA from '../SmartQA.vue';
import { nextTick } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';

// Mock dependencies
vi.mock('@/shared/components/molecules/DynamicGridBackground.vue', () => ({
  default: { template: '<div><slot /></div>' }
}));
vi.mock('@/shared/components/atoms/BaseIcon', () => ({
  default: { template: '<span>icon</span>' }
}));
vi.mock('../AutoTaskPanel.vue', () => ({
  default: { template: '<div class="auto-task-panel">AutoTaskPanel</div>' }
}));
vi.mock('@/features/workflow/components/WorkspaceTabs.vue', () => ({
  default: { template: '<div class="workspace-tabs">WorkspaceTabs</div>' }
}));
vi.mock('../MessageList.vue', () => ({
  default: { template: '<div class="message-list">MessageList</div>' }
}));

// Mock the store
const { mockResetWorkflow, mockInitWorkflow } = vi.hoisted(() => ({
  mockResetWorkflow: vi.fn(),
  mockInitWorkflow: vi.fn(),
}));

vi.mock('@/features/workflow/store/workflow.store', () => ({
  useWorkflowStore: vi.fn(() => ({
    tasks: [],
    isRunning: false,
    progress: 0,
    resetWorkflow: mockResetWorkflow,
    initWorkflow: mockInitWorkflow,
  }))
}));

// Mock Ant Design Vue components
const AntComponents = {
  'a-dropdown': { template: '<div><slot /><slot name="overlay" /></div>' },
  'a-menu': { template: '<div><slot /></div>' },
  'a-menu-item': { template: '<div><slot /></div>' },
  'a-select': { template: '<div><slot /></div>' },
  'a-select-option': { template: '<option><slot /></option>' },
  'a-switch': { template: '<div></div>' },
  'a-progress': { template: '<div></div>' },
  'a-modal': { template: '<div><slot /></div>' },
  'a-tabs': { template: '<div><slot /></div>' },
  'a-tab-pane': { template: '<div><slot /></div>' },
  'a-upload-dragger': { template: '<div><slot /></div>' },
  'a-input': { template: '<input />' },
  'a-button': { template: '<button><slot /></button>' },
  'a-table': { template: '<div></div>' },
};

describe('SmartQA.vue', () => {
  let wrapper;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    mockResetWorkflow.mockClear();
    mockInitWorkflow.mockClear();
    setActivePinia(createPinia());
    
    // Mock fetch
    const fetchMock = vi.fn(() => Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
    }));
    global.fetch = fetchMock;
    window.fetch = fetchMock;

    // Mock window.matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(), // deprecated
        removeListener: vi.fn(), // deprecated
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    // Mount component
    wrapper = mount(SmartQA, {
      props: {
        sessionId: 'session-1'
      },
      global: {
        components: {
          ...AntComponents
        },
        stubs: {
          DynamicGridBackground: { template: '<div><slot /></div>' },
          AutoTaskPanel: true,
          WorkspaceTabs: true,
          MessageList: true,
          BaseIcon: true,
          LoadingOutlined: true,
          StopOutlined: true,
          ArrowUpOutlined: true,
          PaperClipOutlined: true,
          DeleteOutlined: true,
          InboxOutlined: true,
          SearchOutlined: true,
          RobotOutlined: true,
          ProjectOutlined: true,
          MessageOutlined: true,
          DownOutlined: true
        }
      }
    });
  });

  it('resets mode to chat and collapses right pane when sessionId changes', async () => {
    // 1. Simulate changing mode to 'auto_task'
    // Since we mocked a-menu, we can try to emit click on it if we can find it.
    // Or we can cheat and access the internal state if we can.
    // But better: Find the a-menu component and emit the event it listens to.
    
    // In SmartQA.vue: <a-menu @click="({ key }) => handleModeChange(key)">
    
    // Find menu using the component definition directly
    const menus = wrapper.findAllComponents(AntComponents['a-menu']);
    
    if (menus.length > 0) {
        menus[0].vm.$emit('click', { key: 'auto_task' });
    } else {
        console.error('Could not find a-menu component!');
        console.log(wrapper.html());
    }
    
    // Force update because sometimes nextTick is not enough for v-if
    await nextTick();
    await nextTick();
    
    // Verify mode changed to auto_task
    expect(wrapper.findComponent({ name: 'AutoTaskPanel' }).exists()).toBe(true);
    
    // 2. Change sessionId
    await wrapper.setProps({ sessionId: 'session-2' });
    await nextTick();

    // 3. Verify mode is reset to 'chat'
    expect(wrapper.findComponent({ name: 'AutoTaskPanel' }).exists()).toBe(false);
    
    // 4. Verify we are back to chat UI (WorkspaceTabs should NOT exist in chat mode)
    const workspaceTabs = wrapper.findComponent({ name: 'WorkspaceTabs' });
    expect(workspaceTabs.exists()).toBe(false);
  });

  it('resets workflow store when switching sessions', async () => {
    // 1. Switch session
    await wrapper.setProps({ sessionId: 'session-2' });
    await nextTick();
    
    // 2. Verify resetWorkflow is called
    expect(mockResetWorkflow).toHaveBeenCalled();
  });
});
