/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect } from 'vitest';
import LogDrawer from '../LogDrawer.vue';

describe('LogDrawer.vue', () => {
  it('renders logs correctly', () => {
    const logs = [
      { timestamp: 1700000000000, level: 'info', message: 'Test log message' }
    ];
    const wrapper = mount(LogDrawer, {
      props: {
        visible: true,
        logs
      },
      global: {
        stubs: {
          'a-drawer': { template: '<div><slot name="extra"></slot><slot></slot></div>' },
          'a-button': true,
          'a-space': true,
          'DownloadOutlined': true,
          'DeleteOutlined': true
        }
      }
    });

    expect(wrapper.text()).toContain('Test log message');
    expect(wrapper.text()).toContain('info');
  });

  it('emits clear event', async () => {
    const wrapper = mount(LogDrawer, {
      props: { visible: true },
      global: {
        stubs: {
            'a-drawer': { template: '<div><slot name="extra"></slot></div>' },
            'a-button': { template: '<button @click="$emit(\'click\')"></button>' },
            'a-space': { template: '<div><slot></slot></div>' },
            'DownloadOutlined': true,
            'DeleteOutlined': true
        }
      }
    });
    
    // Find buttons. The Clear button is the second one in the template.
    const buttons = wrapper.findAll('button');
    expect(buttons.length).toBe(2);
    await buttons[1].trigger('click');
    
    expect(wrapper.emitted()).toHaveProperty('clear');
  });

  it('renders empty state when no logs', () => {
    const wrapper = mount(LogDrawer, {
      props: {
        visible: true,
        logs: []
      },
      global: {
        stubs: {
          'a-drawer': { template: '<div><slot name="extra"></slot><slot></slot></div>' },
          'a-button': true,
          'a-space': true,
          'DownloadOutlined': true,
          'DeleteOutlined': true,
          'EmptyLogState': true
        }
      }
    });
    
    expect(wrapper.findComponent({ name: 'EmptyLogState' }).exists()).toBe(true);
  });
});
