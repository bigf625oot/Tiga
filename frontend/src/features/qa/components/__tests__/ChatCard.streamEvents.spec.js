/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import ChatCard from '../ChatCard.vue';

vi.mock('@/components/ui/collapsible', () => ({
  Collapsible: { template: '<div><slot /></div>' },
  CollapsibleTrigger: { template: '<div><slot /></div>' },
  CollapsibleContent: { template: '<div><slot /></div>' },
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: { template: '<span><slot /></span>' },
}));

describe('ChatCard stream events', () => {
  it('renders stream events and hides initial loading text when available', () => {
    const message = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      stream_events: [
        { id: 'e1', event: 'status', content: 'Orchestrating context...', ts: 1 },
        { id: 'e2', event: 'status', content: 'Planning tasks...', ts: 2 },
        { id: 'e3', event: 'step', content: 'Initializing Knowledge Base...', ts: 3 },
      ],
    };

    const wrapper = mount(ChatCard, {
      props: {
        message,
        isUser: false,
        showAvatar: false,
        isLast: true,
        isStreaming: true,
        agent: { name: 'Tiga' },
      },
      global: {
        stubs: {
          ChartFrame: true,
          GenericResourceCard: true,
          ThinkingBlock: true,
          ToolStatus: true,
          MarkdownRenderer: true,
          ErrorCallout: true,
        },
      },
    });

    expect(wrapper.text()).toContain('Orchestrating context...');
    expect(wrapper.text()).toContain('Planning tasks...');
    expect(wrapper.text()).toContain('Initializing Knowledge Base...');
    expect(wrapper.text()).not.toContain('正在生成回复...');
  });
});

