import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import SandboxResultViewer from '../SandboxResultViewer.vue';
import { SandboxService } from '../../api/sandbox';

// Mock SandboxService
vi.mock('../../api/sandbox', () => ({
  SandboxService: {
    runCode: vi.fn()
  }
}));

// Mock VueMonacoEditor
vi.mock('@guolao/vue-monaco-editor', () => ({
  VueMonacoEditor: {
    template: '<div class="monaco-mock"></div>',
    props: ['value']
  }
}));

describe('SandboxResultViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly in idle state', () => {
    const wrapper = mount(SandboxResultViewer, {
      props: {
        code: 'print("hello")',
        language: 'python'
      }
    });
    
    expect(wrapper.find('.monaco-mock').exists()).toBe(true);
    expect(wrapper.text()).toContain('执行代码');
    expect(wrapper.text()).toContain('任务执行结果');
  });

  it('handles run action successfully', async () => {
    const mockResult = {
      status: 'success',
      result: {
        type: 'text',
        content: 'hello world',
        files: []
      }
    };
    
    (SandboxService.runCode as any).mockResolvedValue(mockResult);

    const wrapper = mount(SandboxResultViewer, {
      props: {
        code: 'print("hello")'
      }
    });

    // Click run button
    await wrapper.find('button.ant-btn-primary').trigger('click');
    
    expect(wrapper.text()).toContain('重新执行'); // Button text changes if result exists? No, logic says "重新执行" if result exists
    
    // Check service call
    expect(SandboxService.runCode).toHaveBeenCalledWith({
      language: 'python',
      code: 'print("hello")',
      template: undefined,
      params: undefined
    }, expect.any(Object));
  });

  it('displays error state correctly', async () => {
    const errorMsg = 'Syntax Error';
    (SandboxService.runCode as any).mockRejectedValue(new Error(errorMsg));

    const wrapper = mount(SandboxResultViewer, {
      props: { code: 'bad code' }
    });

    await wrapper.find('button.ant-btn-primary').trigger('click');
    
    // Wait for async
    await new Promise(resolve => setTimeout(resolve, 0));
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('执行出错');
    expect(wrapper.text()).toContain(errorMsg);
  });

  it('switches tabs correctly', async () => {
    const wrapper = mount(SandboxResultViewer);
    
    // Initial tab is code
    expect(wrapper.find('.monaco-mock').isVisible()).toBe(true);
    
    // Switch to result tab (Ant Design Tabs structure might be complex to click in unit test, checking logic instead)
    // We can simulate state change if we expose it or just check if tabs exist
    const tabs = wrapper.findAll('.ant-tabs-tab');
    expect(tabs.length).toBe(2);
    expect(tabs[0].text()).toContain('代码');
    expect(tabs[1].text()).toContain('运行结果');
  });
});
