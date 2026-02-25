import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import SmartDataQuery from '../SmartDataQuery.vue';
import { nextTick } from 'vue';

// Mock ant-design-vue message
vi.mock('ant-design-vue', () => ({
  message: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  }
}));

// Mock icons
const MockIcon = { template: '<span></span>' };
const stubs = {
    'CheckCircleOutlined': MockIcon,
    'CloseCircleOutlined': MockIcon,
    'InfoCircleOutlined': MockIcon,
    'a-form': { template: '<form><slot /></form>' },
    'a-form-item': { template: '<div><slot /></div>' },
    'a-input': { template: '<input />' },
    'a-select': { template: '<select><slot /></select>' },
    'a-select-option': { template: '<option><slot /></option>' },
    'a-input-number': { template: '<input type="number" />' },
    'a-input-password': { template: '<input type="password" />' },
    'a-button': { template: '<button><slot /></button>' }
};

describe('SmartDataQuery.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('computes validation rules correctly for SQLite', async () => {
    const wrapper = mount(SmartDataQuery, {
      global: { stubs }
    });

    // Default is sqlite
    expect(wrapper.vm.config.type).toBe('sqlite');
    
    // Check rules
    const rules = wrapper.vm.rules;
    expect(rules.path).toBeDefined();
    expect(rules.host).toBeUndefined();
    expect(rules.port).toBeUndefined();
    expect(rules.user).toBeUndefined();
  });

  it('computes validation rules correctly for MySQL', async () => {
    const wrapper = mount(SmartDataQuery, {
      global: { stubs }
    });

    // Change to mysql
    wrapper.vm.config.type = 'mysql';
    await nextTick();
    
    const rules = wrapper.vm.rules;
    expect(rules.path).toBeUndefined();
    expect(rules.host).toBeDefined();
    expect(rules.port).toBeDefined();
    expect(rules.user).toBeDefined();
  });

  it('sendMessage handles streaming response correctly', async () => {
    const wrapper = mount(SmartDataQuery, {
      global: { stubs }
    });

    // Mock fetch response with a stream
    const stream = new ReadableStream({
        start(controller) {
            controller.enqueue(new TextEncoder().encode('Hello '));
            controller.enqueue(new TextEncoder().encode('World'));
            controller.close();
        }
    });

    global.fetch.mockResolvedValue({
        ok: true,
        body: stream
    });

    // Set input
    wrapper.vm.input = 'Test Question';
    
    // Call sendMessage
    await wrapper.vm.sendMessage();
    
    // Wait for async operations
    await new Promise(resolve => setTimeout(resolve, 100));

    // Check messages
    const messages = wrapper.vm.messages;
    expect(messages.length).toBe(2);
    expect(messages[0]).toEqual({ role: 'user', content: 'Test Question' });
    expect(messages[1].role).toBe('assistant');
    expect(messages[1].content).toBe('Hello World');
    expect(wrapper.vm.isLoading).toBe(false);
  });

  it('sendMessage handles error during fetch', async () => {
    const wrapper = mount(SmartDataQuery, {
      global: { stubs }
    });

    global.fetch.mockRejectedValue(new Error('Network Error'));

    wrapper.vm.input = 'Test Question';
    await wrapper.vm.sendMessage();
    
    const messages = wrapper.vm.messages;
    expect(messages.length).toBe(2);
    expect(messages[1].content).toContain('Error: Network Error');
    expect(wrapper.vm.isLoading).toBe(false);
  });
});
