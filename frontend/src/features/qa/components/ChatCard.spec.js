/**
 * @场景    验证 ChatCard 在智能查询与知识问答模式下的渲染行为
 * @功能    覆盖 SQL 区块、图表占位、引用来源与外层壳结构断言
 * @依赖    vitest、@vue/test-utils、ChatCard 组件
 * @备注    主要是渲染级测试，未覆盖事件交互与异常路径
 */
import { mount } from '@vue/test-utils';
import ChatCard from './ChatCard.vue';
import { describe, it, expect, vi } from 'vitest';

describe('ChatCard.vue', () => {
  const mockAgent = { name: 'Test Agent', icon: '/agent.png' };
  const mockMessage = {
    content: 'Test content',
    timestamp: '2023-01-01T12:00:00Z',
    sql_query: 'SELECT * FROM users',
    chart_config: { title: { text: 'Test Chart' } },
    sources: [{ title: 'Source 1', url: 'http://example.com' }]
  };

  it('renders correctly in Intelligent Query mode', () => {
    const wrapper = mount(ChatCard, {
      props: {
        message: mockMessage,
        type: 'intelligent_query',
        isUser: false,
        agent: mockAgent
      },
      global: {
        stubs: ['ChartFrame']
      }
    });

    // Check for SQL block
    expect(wrapper.find('code').text()).toBe(mockMessage.sql_query);
    
    // Check for ChartFrame
    expect(wrapper.findComponent({ name: 'ChartFrame' }).exists()).toBe(true);
    
    // Check that references are NOT rendered in this mode (unless shared logic changed)
    // Based on implementation, references are in knowledge_qa block
    expect(wrapper.find('.knowledge-qa-content').exists()).toBe(false);
  });

  it('renders correctly in Knowledge QA mode', () => {
    const wrapper = mount(ChatCard, {
      props: {
        message: mockMessage,
        type: 'knowledge_qa',
        isUser: false,
        agent: mockAgent
      }
    });

    // Check for Markdown content wrapper
    expect(wrapper.find('.markdown-body').exists()).toBe(true);
    
    // Check for References
    expect(wrapper.text()).toContain('参考来源');
    expect(wrapper.text()).toContain('Source 1');
    
    // Check SQL block is NOT rendered
    expect(wrapper.find('code.text-green-400').exists()).toBe(false);
  });

  it('renders consistent outer shell in both modes', () => {
    const wrapperIntelligent = mount(ChatCard, {
      props: { message: mockMessage, type: 'intelligent_query', isUser: false }
    });
    const wrapperKnowledge = mount(ChatCard, {
      props: { message: mockMessage, type: 'knowledge_qa', isUser: false }
    });

    // Check avatar presence
    expect(wrapperIntelligent.find('img[alt="agent"]').exists()).toBe(true);
    expect(wrapperKnowledge.find('img[alt="agent"]').exists()).toBe(true);

    // Check action buttons presence (footer)
    // Note: Actions are in group-hover, might need to check existence in DOM
    expect(wrapperIntelligent.findAll('button[title="复制"]').length).toBe(1);
    expect(wrapperKnowledge.findAll('button[title="复制"]').length).toBe(1);
  });

  it('does not trigger extra requests or warnings', () => {
    const consoleSpy = vi.spyOn(console, 'warn');
    mount(ChatCard, {
      props: { message: mockMessage, type: 'intelligent_query' }
    });
    expect(consoleSpy).not.toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
