import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import KnowledgeGraphView from '../KnowledgeGraphView.vue';

vi.mock('ant-design-vue', async () => {
  const message = { warning: vi.fn(), success: vi.fn(), info: vi.fn(), error: vi.fn() };
  const Modal = { warning: vi.fn(), info: vi.fn(), confirm: vi.fn() };
  return { message, Modal };
});

vi.mock('@/shared/components/organisms/GraphViewer', () => ({
  GraphViewer: { template: '<div class="graph-viewer-stub"></div>' }
}));

describe('KnowledgeGraphView.vue', () => {
  const mountComp = () => mount(KnowledgeGraphView, {
    props: { docId: 1, initialScope: 'doc' },
    global: {
      stubs: {}
    }
  });

  it('renderMarkdown: renders clickable [n] when hasSources=true', () => {
    const wrapper = mountComp();
    const html = wrapper.vm.renderMarkdown('引用 [1] 内容', true);
    expect(html).toContain('citation-icon');
    expect(html).not.toContain('citation-index-disabled');
  });

  it('renderMarkdown: renders disabled [n] when hasSources=false', () => {
    const wrapper = mountComp();
    const html = wrapper.vm.renderMarkdown('引用 [2] 内容', false);
    expect(html).toContain('citation-index-disabled');
    expect(html).not.toContain('citation-icon');
  });

  it('handleCitationClick: does nothing when sources empty (no warning)', async () => {
    const wrapper = mountComp();
    const container = document.createElement('div');
    container.innerHTML = wrapper.vm.renderMarkdown('引用 [1] 内容', false);
    const target = container.querySelector('.citation-index-disabled');
    const event = { target, stopPropagation: vi.fn() };
    const msg = { content: '引用 [1] 内容', sources: [] };
    wrapper.vm.handleCitationClick(event, msg);
    const { Modal } = await import('ant-design-vue');
    expect(Modal.warning).not.toHaveBeenCalled();
  });
});
