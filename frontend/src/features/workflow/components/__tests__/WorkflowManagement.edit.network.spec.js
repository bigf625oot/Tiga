/**
 * @vitest-environment jsdom
 */
import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import WorkflowManagement from '../WorkflowManagement.vue';

// Mock ant-design-vue message with hoisted var
const { msg } = vi.hoisted(() => ({
  msg: { success: vi.fn(), error: vi.fn() }
}));
vi.mock('ant-design-vue', () => {
  return { message: msg };
});

describe('WorkflowManagement edit failure', () => {
  it('shows error when PUT fails during edit', async () => {
    // Mock fetch: edit PUT not ok
    global.fetch = vi.fn().mockResolvedValueOnce({ ok: false, json: async () => ({ detail: 'bad' }) });

    const wrapper = mount(WorkflowManagement, {
      global: {
        stubs: {
          Loading: { template: '<div />' },
          'a-modal': {
            emits: ['ok', 'update:open'],
            props: ['open', 'title'],
            template: '<div class="stub-modal"><slot /></div>'
          }
        }
      }
    });

    // Prepare edit state
    wrapper.vm.editWorkflow({ id: 'wf-1', name: 'Old', webhook_url: 'http://x', description: 'd', is_active: true });
    // Trigger submit (PUT)
    await wrapper.vm.handleSubmit();
    expect(msg.error).toHaveBeenCalled();
  });
});
