/**
 * @场景    验证消息中 think 标签（闭合/未闭合）在 UI 中的解析展示
 * @功能    覆盖 details 折叠块渲染与正文保留逻辑
 * @依赖    vitest、@vue/test-utils、MessageItem 组件
 * @备注    该测试绑定 MessageItem；若收敛到 ChatCard 需迁移用例
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import MessageItem from '../MessageItem.vue';

describe('MessageItem.vue', () => {
  it('renders unclosed <think> tags inside a details block', () => {
    const message = {
      role: 'assistant',
      content: 'Here is some text. <think>This is unclosed thinking...',
      timestamp: new Date().toISOString()
    };
    
    const wrapper = mount(MessageItem, {
      props: {
        message,
        isUser: false
      },
      global: {
        stubs: {
            ChartFrame: true,
            SourcePanel: true,
            BaseIcon: true
        }
      }
    });
    
    // The component uses v-html, so we check the DOM
    const details = wrapper.find('details');
    expect(details.exists()).toBe(true);
    expect(details.text()).toContain('This is unclosed thinking...');
    expect(details.attributes('open')).toBeDefined(); // Should be open for partial/unclosed
    
    // Verify "Here is some text." is outside (or handled)
    // The logic: 
    // inputText = inputText.substring(0, thinkStart);
    // return thinkHtml + html;
    // So "Here is some text." should be rendered after the details block (or before?)
    // Wait, the logic is `return thinkHtml + html;`
    // thinkHtml is the details block.
    // html is the parsed markdown of `inputText`.
    // If `inputText` was "Here is some text. ", it should be there.
    
    expect(wrapper.text()).toContain('Here is some text.');
  });

  it('renders closed <think> tags inside a details block', () => {
    const message = {
      role: 'assistant',
      content: '<think>Closed thinking</think> Final answer.',
      timestamp: new Date().toISOString()
    };
    
    const wrapper = mount(MessageItem, {
      props: {
        message,
        isUser: false
      },
      global: {
        stubs: {
            ChartFrame: true,
            SourcePanel: true,
            BaseIcon: true
        }
      }
    });
    
    const details = wrapper.find('details');
    expect(details.exists()).toBe(true);
    expect(details.text()).toContain('Closed thinking');
    expect(wrapper.text()).toContain('Final answer.');
  });
});
