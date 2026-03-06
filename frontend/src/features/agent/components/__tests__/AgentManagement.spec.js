/**
 * @vitest-environment jsdom
 */
import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AgentManagement from '../AgentManagement.vue';

// Mock ant-design-vue Modal & message (use hoisted to avoid init ordering issues)
const { modalConfirm } = vi.hoisted(() => ({
  modalConfirm: vi.fn((opts) => { opts.onOk && opts.onOk(); })
}));
vi.mock('ant-design-vue', () => {
  return {
    Modal: { confirm: modalConfirm },
    message: { success: vi.fn(), error: vi.fn() }
  };
});

// Mock child components
const stubs = {
  Loading: { template: '<div class="stub-loading"></div>' },
  AgentCard: { template: '<div class="stub-agent-card">Agent</div>' },
  UserScriptsEditor: { template: '<div class="stub-user-scripts"></div>' }
};

describe('AgentManagement.vue', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    window.alert = vi.fn();
  });

  it('opens create modal and saves new agent', async () => {
    const wrapper = mount(AgentManagement, { global: { stubs } });
    // Simulate loading completed
    (wrapper.vm.isLoading = false);
    await flushPromises();
    // Open modal
    const createBtn = wrapper.findAll('button').find(b => b.text().includes('创建智能体'));
    expect(createBtn).toBeTruthy();
    await createBtn.trigger('click');
    expect(wrapper.text()).toContain('新建智能体');
    // Fill name and save
    wrapper.vm.form.name = 'Test Agent';
    // Mock POST response
    global.fetch = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ id: '1' }) });
    const saveBtn = wrapper.findAll('button').find(b => b.text().includes('保存配置'));
    await saveBtn.trigger('click');
    await flushPromises();
    // Verify POST call exists
    const postCall = global.fetch.mock.calls.find(call => call[0] === '/api/v1/agents/' && call[1]?.method === 'POST');
    expect(postCall).toBeTruthy();
  });

  it('edits existing agent and saves via PUT', async () => {
    const wrapper = mount(AgentManagement, { global: { stubs } });
    (wrapper.vm.isLoading = false);
    await flushPromises();
    // Call editAgent directly
    wrapper.vm.editAgent({ id: 'a1', name: 'Old', description: 'D' });
    await flushPromises();
    expect(wrapper.text()).toContain('编辑智能体');
    // Change name
    wrapper.vm.form.name = 'New Name';
    // Mock PUT
    global.fetch = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    const saveBtn = wrapper.findAll('button').find(b => b.text().includes('保存配置'));
    await saveBtn.trigger('click');
    await flushPromises();
    const call = global.fetch.mock.calls[0];
    expect(call[0]).toBe('/api/v1/agents/a1');
    expect(call[1].method).toBe('PUT');
  });

  it('deletes agent via Modal.confirm', async () => {
    const wrapper = mount(AgentManagement, { global: { stubs } });
    (wrapper.vm.isLoading = false);
    await flushPromises();
    global.fetch = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    await wrapper.vm.deleteAgent({ id: 'a2', name: 'ToDelete' });
    expect(modalConfirm).toHaveBeenCalled();
    const call = global.fetch.mock.calls[0];
    expect(call[0]).toBe('/api/v1/agents/a2');
    expect(call[1].method).toBe('DELETE');
  });
});
