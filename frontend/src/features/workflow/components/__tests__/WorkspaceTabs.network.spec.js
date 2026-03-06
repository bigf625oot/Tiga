/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import WorkspaceTabs from '../WorkspaceTabs.vue';
import { vi } from 'vitest';

// Mock GraphViewer module to avoid loading 3D libs
const { GraphStubComp } = vi.hoisted(() => ({
  GraphStubComp: {
    props: ['nodes', 'edges', 'loading', 'scope'],
    template: '<div class="graph-viewer">{{ loading }}</div>'
  }
}));
vi.mock('@/shared/components/organisms/GraphViewer/GraphViewer.vue', () => {
  return { default: GraphStubComp };
});

describe('WorkspaceTabs network error handling', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });
  it('handles graph load failure during locateNode', async () => {
    // Stub GraphViewer to observe loading prop
    // Mock fetch to reject
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    const wrapper = mount(WorkspaceTabs, {
      props: { isWorkflowMode: true },
      global: {
        stubs: {
          TaskPanel: true,
          DocumentPanel: true,
          CodeOutlined: true
        }
      }
    });

    // Call exposed locateNode which triggers loadGraph
    await wrapper.vm.locateNode('n1', 123);
    // After error, component should still render GraphViewer and loading should be false
    const gv = wrapper.find('.graph-viewer');
    expect(gv.exists()).toBe(true);
    expect(gv.text()).toBe('false');
  });
});
