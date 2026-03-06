/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import WorkspaceTabs from '../WorkspaceTabs.vue';
// Mock GraphViewer to expose scope prop text (hoisted)
const { GraphStubComp } = vi.hoisted(() => ({
  GraphStubComp: {
    props: ['nodes', 'edges', 'loading', 'scope'],
    template: '<div class="graph-viewer-scope">{{ scope }}</div>'
  }
}));
vi.mock('@/shared/components/organisms/GraphViewer/GraphViewer.vue', () => {
  return { default: GraphStubComp };
});

describe('WorkspaceTabs scope switching', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('switches to doc scope when locating node with docId', async () => {
    // Mock fetch for doc graph
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes('/knowledge/123/graph')) {
        return { ok: true, json: async () => ({ nodes: { a: {} }, edges: {} }) };
      }
      return { ok: true, json: async () => ({ nodes: {}, edges: {} }) };
    });

    const wrapper = mount(WorkspaceTabs, {
      props: { isWorkflowMode: true },
      global: {
        stubs: { TaskPanel: true, DocumentPanel: true, CodeOutlined: true }
      }
    });

    await wrapper.vm.locateNode('n-1', 123);
    const gv = wrapper.find('.graph-viewer-scope');
    expect(gv.exists()).toBe(true);
    expect(gv.text()).toBe('doc');
  });

  it('switches back to global scope when locating without docId', async () => {
    // Mock fetch for global graph
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes('/knowledge/graph')) {
        return { ok: true, json: async () => ({ nodes: { g: {} }, edges: {} }) };
      }
      return { ok: true, json: async () => ({ nodes: {}, edges: {} }) };
    });

    const wrapper = mount(WorkspaceTabs, {
      props: { isWorkflowMode: true },
      global: {
        stubs: { TaskPanel: true, DocumentPanel: true, CodeOutlined: true }
      }
    });

    await wrapper.vm.locateNode('n-2', null);
    const gv = wrapper.find('.graph-viewer-scope');
    expect(gv.exists()).toBe(true);
    expect(gv.text()).toBe('global');
  });
});
