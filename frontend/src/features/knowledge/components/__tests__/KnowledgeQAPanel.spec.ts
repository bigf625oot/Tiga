import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import KnowledgeQAPanel from '../KnowledgeQAPanel.vue';
import { nextTick } from 'vue';

// Mock dependencies
vi.mock('ant-design-vue', () => {
  return {
    message: { 
        warning: vi.fn(), 
        success: vi.fn(), 
        info: vi.fn(), 
        error: vi.fn() 
    },
    Modal: { 
        warning: vi.fn(), 
        info: vi.fn(), 
        confirm: vi.fn() 
    }
  };
});

vi.mock('axios', () => ({
    default: {
        create: () => ({
            get: vi.fn().mockResolvedValue({ data: [] }),
            delete: vi.fn().mockResolvedValue({}),
            post: vi.fn().mockResolvedValue({})
        })
    }
}));

// Mock fetch
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    body: {
      getReader: () => ({
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('{"type":"text","content":"Hello"}') })
          .mockResolvedValueOnce({ done: true })
      })
    }
  })
) as any;

describe('KnowledgeQAPanel.vue', () => {
    let wrapper: any;

    beforeEach(() => {
        wrapper = mount(KnowledgeQAPanel, {
            props: {
                visible: true,
                docId: 1,
                scope: 'doc',
                nodes: {
                    'node1': { name: 'Entity1' },
                    'node2': { name: 'Entity2' }
                }
            },
            global: {
                stubs: {
                    ChartFrame: true
                }
            }
        });
    });

    it('renderMarkdown: renders clickable [n] when hasStructuredSources=true', async () => {
        const msg = { 
            _id: 'msg1', 
            role: 'assistant', 
            content: '引用 [1] 内容', 
            sources: [{ title: 's1', source: 'vector' }] 
        };
        wrapper.vm.chatMessages = [msg];
        await nextTick();
        
        const html = wrapper.find('.markdown-content').html();
        expect(html).toContain('citation-icon');
        expect(html).not.toContain('citation-index-disabled');
    });

    it('renderMarkdown: renders disabled [n] when sources empty', async () => {
        const msg = { 
            _id: 'msg2', 
            role: 'assistant', 
            content: '引用 [1] 内容', 
            sources: [] 
        };
        wrapper.vm.chatMessages = [msg];
        await nextTick();
        
        const html = wrapper.find('.markdown-content').html();
        expect(html).toContain('citation-index-disabled');
    });

    it('handleCitationClick: emits locate-node when graph source clicked', async () => {
        const msg = {
            _id: 'msg3',
            role: 'assistant',
            content: '引用 [1] 内容',
            sources: [{ title: 'Entity1', source: 'graph' }]
        };
        wrapper.vm.chatMessages = [msg];
        await nextTick();

        // Simulate click
        const container = wrapper.find('.markdown-content');
        const citationIcon = document.createElement('span');
        citationIcon.classList.add('citation-icon');
        citationIcon.setAttribute('data-idx', '0');
        
        const event = {
            target: citationIcon,
            stopPropagation: vi.fn(),
            closest: (sel: string) => (sel === '.citation-icon' ? citationIcon : null)
        };
        
        // Since we exposed handleCitationClick
        wrapper.vm.handleCitationClick(event, msg);
        
        expect(wrapper.emitted('locate-node')).toBeTruthy();
        expect(wrapper.emitted('locate-node')[0]).toEqual(['node1']);
    });

    it('sendChatMessage: adds user message and calls fetch', async () => {
        wrapper.vm.chatInput = 'Test Query';
        await wrapper.vm.sendChatMessage();
        
        expect(wrapper.vm.chatMessages.length).toBeGreaterThan(0);
        expect(wrapper.vm.chatMessages[0].content).toBe('Test Query');
        expect(global.fetch).toHaveBeenCalled();
    });
});
