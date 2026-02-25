import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import SandboxResultViewer from '../SandboxResultViewer.vue';
import { SandboxService } from '../../api/sandbox';

// Mock i18n
vi.mock('../../../../locales', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}));

// Mock SandboxService

// Mock components
const stubs = {
    'a-button': { template: '<button><slot /></button>' },
    'el-image': { template: '<div></div>' },
    'el-carousel': { template: '<div><slot /></div>' },
    'el-carousel-item': { template: '<div><slot /></div>' },
    'AppstoreOutlined': { template: '<span></span>' },
    'FileImageOutlined': { template: '<span></span>' },
    'CloseCircleFilled': { template: '<span></span>' }
};

describe('SandboxResultViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly in idle state (empty)', () => {
    const wrapper = mount(SandboxResultViewer, {
      props: {
        code: 'print("hello")'
      },
      global: { stubs }
    });
    
    // Should show empty state
    expect(wrapper.text()).toContain('sandbox.status.noData'); // Using key because i18n mock returns key
  });

  it('renders result content when available', async () => {
    const wrapper = mount(SandboxResultViewer, {
      props: {
        code: 'print("hello")'
      },
      global: { stubs }
    });

    // Simulate result
    wrapper.vm.result = {
      status: 'success',
      content: 'Hello World',
      files: []
    };
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('Hello World');
    expect(wrapper.text()).toContain('sandbox.output.preview');
  });

  it('displays error state correctly', async () => {
    const wrapper = mount(SandboxResultViewer, {
      props: { code: 'bad code' },
      global: { stubs }
    });

    // Simulate error
    wrapper.vm.error = { message: 'Syntax Error' };
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('sandbox.status.error');
    expect(wrapper.text()).toContain('Syntax Error');
  });

  it('switches tabs correctly', async () => {
    const wrapper = mount(SandboxResultViewer, {
        global: { stubs }
    });
    
    // Default tab is result
    expect(wrapper.text()).toContain('sandbox.status.noData'); // Empty result
    
    // Switch to env tab
    const buttons = wrapper.findAll('button');
    // Assuming 2nd button is env tab (index 1)
    await buttons[1].trigger('click');
    
    expect(wrapper.text()).toContain('sandbox.env.title');
    expect(wrapper.text()).toContain('Python 3.10');
  });
});
