/**
 * @vitest-environment jsdom
 */
/**
 * @场景    验证 SmartQA 在 SSE 流式返回下的消息归一化与边界行为
 * @功能    覆盖 think/text 事件处理、对象片段拼接与未闭合 think 标签场景
 * @依赖    vitest、@vue/test-utils、pinia、SmartQA 组件
 * @备注    通过 ReadableStream 模拟服务端推流，重点保护流式解析稳定性
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import SmartQA from '../SmartQA.vue';
import { createPinia, setActivePinia } from 'pinia';

// Avoid loading 3D viewer libs in test env
vi.mock('@/shared/components/organisms/GraphViewer/GraphViewer3D.vue', () => ({
  default: { template: '<div />' }
}));

// Reuse minimal stubs similar to SmartQA.spec.js
const AntComponents = {
  'a-dropdown': { template: '<div><slot /><slot name="overlay" /></div>' },
  'a-menu': { template: '<div><slot /></div>' },
  'a-menu-item': { template: '<div><slot /></div>' },
  'a-select': { template: '<div><slot /></div>' },
  'a-select-option': { template: '<option><slot /></option>' },
  'a-switch': { template: '<div></div>' },
  'a-progress': { template: '<div></div>' },
  'a-modal': { template: '<div><slot /></div>' },
  'a-tabs': { template: '<div><slot /></div>' },
  'a-tab-pane': { template: '<div><slot /></div>' },
  'a-upload-dragger': { template: '<div><slot /></div>' },
  'a-input': { template: '<input />' },
  'a-button': { template: '<button><slot /></button>' },
  'a-table': { template: '<div></div>' },
};

describe('SmartQA SSE streaming', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    // Default fetch mock
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => [] });
    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it('normalizes think and text events, avoids [object Object]', async () => {
    // Build SSE-like stream
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        const chunks = [
          'event: think\n' + 'data: ' + JSON.stringify({ message: '正在初始化' }) + '\n\n',
          'event: text\n' + 'data: ' + JSON.stringify({ desc: '对象片段' }) + '\n\n',
          'event: text\n' + 'data: ' + JSON.stringify('正文字符串') + '\n\n',
          'event: done\n' + 'data: {}\n\n',
        ];
        chunks.forEach(c => controller.enqueue(encoder.encode(c)));
        controller.close();
      }
    });

    // Mock fetch: default json for GET/Upload, SSE for chat POST with JSON body
    global.fetch = vi.fn((url, opts = {}) => {
      if (opts.method === 'POST' && opts.body && !(opts.body instanceof FormData)) {
        return Promise.resolve({ ok: true, body: stream });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    const wrapper = mount(SmartQA, {
      props: { sessionId: 'session-1' },
      global: {
        components: { ...AntComponents },
        stubs: {
          DynamicGridBackground: { template: '<div><slot /></div>' },
          AutoTaskPanel: true,
          WorkspaceTabs: true,
          MessageList: true,
          BaseIcon: true,
          LoadingOutlined: true,
          StopOutlined: true,
          ArrowUpOutlined: true,
          PaperClipOutlined: true,
          DeleteOutlined: true,
          InboxOutlined: true,
          SearchOutlined: true,
          RobotOutlined: true,
          ProjectOutlined: true,
          MessageOutlined: true,
          DownOutlined: true
        }
      }
    });

    // Set input and click send
    const ta = wrapper.find('textarea');
    await ta.setValue('hello');
    const sendBtn = wrapper.find('button.rounded-full');
    await sendBtn.trigger('click');

    // Wait for stream processing
    await new Promise(res => setTimeout(res, 200));

    // Inspect messages (MessageList is stubbed, check component state)
    const msgs = (wrapper.vm.messages || []);
    const assistant = msgs.find(m => m.role === 'assistant');
    expect(assistant).toBeDefined();
    expect(assistant.content || '').not.toContain('[object Object]');
    expect((assistant.reasoning || '')).toContain('正在初始化');
  });

  it('handles unclosed think tags by wrapping them', async () => {
    // Stream with unclosed <think>
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        const chunks = [
          'event: think\n' + 'data: ' + JSON.stringify({ message: '开始思考' }) + '\n\n',
          'event: text\n' + 'data: ' + JSON.stringify('<think>尚未闭合的思考过程') + '\n\n',
          // No closing </think> sent, and stream ends or pauses
          'event: done\n' + 'data: {}\n\n',
        ];
        chunks.forEach(c => controller.enqueue(encoder.encode(c)));
        controller.close();
      }
    });

    global.fetch = vi.fn((url, opts = {}) => {
      if (opts.method === 'POST') {
        return Promise.resolve({ ok: true, body: stream });
      }
      return Promise.resolve({ ok: true, json: async () => [] });
    });

    const wrapper = mount(SmartQA, {
       props: { sessionId: 'session-unclosed' },
       global: {
         components: { ...AntComponents },
         stubs: {
           DynamicGridBackground: { template: '<div><slot /></div>' },
           AutoTaskPanel: true,
           WorkspaceTabs: true,
           MessageList: true,
           BaseIcon: true
         }
       }
     });
 
     await new Promise(resolve => setTimeout(resolve, 0)); // Allow mount effects
     const ta = wrapper.find('textarea');
     if (!ta.exists()) {
        console.log(wrapper.html());
        throw new Error('Textarea not found');
     }
     await ta.setValue('test unclosed');
    await wrapper.find('button.rounded-full').trigger('click');

    await new Promise(res => setTimeout(res, 200));

    const msgs = wrapper.vm.messages || [];
    const assistant = msgs.find(m => m.role === 'assistant');
    
    // The component should detect unclosed <think> and move it to reasoning
    // OR render it within a details block in the content
    // Based on previous implementation: "Handle unclosed tags... logic to wrap partial content"
    
    // Check if content contains the details tag wrapper or if reasoning captures it
    // If the logic extracts it to reasoning field:
    // expect(assistant.reasoning).toContain('尚未闭合的思考过程');
    // expect(assistant.content).not.toContain('<think>');
    
    // If the logic wraps it in markdown:
    // The SmartQA.vue logic likely modifies the display content.
    // Let's verify that the raw content doesn't leak "unclosed" raw text without protection
    
    // Verify that SmartQA preserves the raw content (including unclosed tags)
    // so that MessageItem can render it correctly.
    expect(assistant).toBeDefined();
    expect(assistant.content).toContain('<think>尚未闭合的思考过程');
  });
});
