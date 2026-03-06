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

describe('WorkflowManagement network error', () => {
  it('shows error when submit fails', async () => {
    // Mock fetch to return not ok
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

    // Open modal
    await wrapper.vm.openRegisterModal();
    // Fill form via vm
    wrapper.vm.form.name = 'WF';
    wrapper.vm.form.webhook_url = 'http://x';
    // Trigger submit
    await wrapper.vm.handleSubmit();
    expect(msg.error).toHaveBeenCalled();
  });
});
