/**
 * @vitest-environment jsdom
 */
import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ServiceMarket from '../ServiceMarket.vue';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock alert and confirm
window.alert = vi.fn();
window.confirm = vi.fn();

describe('ServiceMarket.vue', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    window.alert.mockReset();
    window.confirm.mockReset();

    // Default mock response for initial data loading
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => [] // Default empty list for categories, skills, mcp
    });
  });

  it('opens create tool modal when clicking create button', async () => {
    const wrapper = mount(ServiceMarket);
    
    // Find the create tool button (in the sidebar)
    const createBtn = wrapper.findAll('button').find(b => b.text().includes('创建工具'));
    expect(createBtn.exists()).toBe(true);
    
    await createBtn.trigger('click');
    expect(wrapper.find('.fixed.inset-0').exists()).toBe(true);
    expect(wrapper.text()).toContain('创建新工具');
  });

  it('validates required fields for Skill creation', async () => {
    const wrapper = mount(ServiceMarket);
    
    // Open modal
    const createBtn = wrapper.findAll('button').find(b => b.text().includes('创建工具'));
    await createBtn.trigger('click');
    
    // Click submit without filling anything
    const submitBtn = wrapper.findAll('button').find(b => b.text().includes('确认创建'));
    await submitBtn.trigger('click');
    
    expect(window.alert).toHaveBeenCalledWith('请输入工具名称');
  });

  it('creates an Agent Skill successfully', async () => {
    const wrapper = mount(ServiceMarket);
    
    // Open modal
    await wrapper.findAll('button').find(b => b.text().includes('创建工具')).trigger('click');
    
    // Fill form
    const inputs = wrapper.findAll('input[type="text"]');
    const nameInput = inputs.find(i => i.element.placeholder.includes('codemap'));
    const versionInput = inputs.find(i => i.element.placeholder.includes('1.0.0'));
    
    await nameInput.setValue('Test Skill');
    await versionInput.setValue('1.0.1');
    
    // Fill content (textarea)
    const textareas = wrapper.findAll('textarea');
    // The content textarea has placeholder starting with "当这个 Skill..."
    const contentTextarea = textareas.find(t => t.element.placeholder.includes('当这个 Skill'));
    await contentTextarea.setValue('# Test Command');
    
    // Mock successful creation response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: '123', name: 'Test Skill' })
    });

    // Click submit
    const submitBtn = wrapper.findAll('button').find(b => b.text().includes('确认创建'));
    await submitBtn.trigger('click');
    
    await flushPromises();
    
    // Verify fetch call
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/skills/', expect.objectContaining({
      method: 'POST',
      body: expect.stringContaining('"name":"Test Skill"')
    }));
    
    const postCall = mockFetch.mock.calls.find(call => call[0] === '/api/v1/skills/' && call[1].method === 'POST');
    const callArgs = JSON.parse(postCall[1].body);
    expect(callArgs).toMatchObject({
      name: 'Test Skill',
      version: '1.0.1',
      content: '# Test Command',
      meta_data: { scope: 'global' } // default scope
    });
  });

  it('creates an MCP Server successfully', async () => {
    const wrapper = mount(ServiceMarket);
    
    // Open modal
    await wrapper.findAll('button').find(b => b.text().includes('创建工具')).trigger('click');
    
    // Switch to MCP type
    // Find the div that contains "MCP Server" text and trigger click
    // Note: The structure is a div with @click="newToolForm.type = 'mcp'"
    // We can find it by looking for the text "MCP Server"
    const mcpTextDiv = wrapper.findAll('div').find(d => d.text() === 'MCP Server');
    // The clickable element is likely the parent or grandparent of the text node
    // Let's try to find the clickable container directly
    // Based on the code: <div @click="..." class="... flex items-start gap-3">
    const typeCards = wrapper.findAll('.cursor-pointer.border-2');
    const mcpCard = typeCards.find(c => c.text().includes('MCP Server'));
    
    expect(mcpCard.exists()).toBe(true);
    await mcpCard.trigger('click');
    
    // Fill form
    const inputs = wrapper.findAll('input[type="text"]');
    const nameInput = inputs.find(i => i.element.placeholder.includes('codemap'));
    const versionInput = inputs.find(i => i.element.placeholder.includes('1.0.0'));
    
    await nameInput.setValue('Test MCP');
    await versionInput.setValue('2.0.0');
    
    // Fill MCP config
    // The mcp config textarea is visible when type is MCP and has bg-slate-900 class
    const mcpConfigTextarea = wrapper.find('textarea.bg-slate-900');
    expect(mcpConfigTextarea.exists()).toBe(true);
    
    const validConfig = JSON.stringify({ command: 'node', args: ['index.js'] });
    await mcpConfigTextarea.setValue(validConfig);
    
    // Mock successful creation response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: '456', name: 'Test MCP' })
    });

    // Click submit
    const submitBtn = wrapper.findAll('button').find(b => b.text().includes('确认创建'));
    await submitBtn.trigger('click');
    
    await flushPromises();
    
    // Verify fetch call
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/mcp/', expect.objectContaining({
      method: 'POST',
      body: expect.stringContaining('"name":"Test MCP"')
    }));
    
    const postCall = mockFetch.mock.calls.find(call => call[0] === '/api/v1/mcp/' && call[1].method === 'POST');
    const callArgs = JSON.parse(postCall[1].body);
    expect(callArgs).toMatchObject({
      name: 'Test MCP',
      type: 'stdio', // default
      config: { command: 'node', args: ['index.js'] }
    });
  });
});
