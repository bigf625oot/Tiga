import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useChatSession } from '../useChatSession';
import { chatService } from '@/features/llm-chat/services/chatService';
import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';

// Mock dependencies
vi.mock('@/features/llm-chat/services/chatService', () => ({
  chatService: {
    getSession: vi.fn(),
    createSession: vi.fn(),
    sendChatMessage: vi.fn(),
  }
}));

vi.mock('@/components/ui/toast/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

describe('useChatSession', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    delete window._lastStreamEndTime;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('1. should create a new session successfully', async () => {
    const mockSession = { id: 'sess-1', mode: 'quick', workflow_state: {} };
    vi.mocked(chatService.createSession).mockResolvedValue(mockSession as any);

    const { createNewSession, currentSessionId, currentSession } = useChatSession();
    
    const result = await createNewSession('Hello', 'agent-1', 'quick');
    
    expect(result).toEqual(mockSession);
    expect(currentSessionId.value).toBe('sess-1');
    expect(currentSession.value).toEqual(mockSession);
  });

  it('2. should fetch session details and merge messages', async () => {
    const mockSessionData = {
      id: 'sess-2',
      mode: 'quick',
      messages: [
        { id: 'msg-1', role: 'user', content: 'Hi' }
      ]
    };
    vi.mocked(chatService.getSession).mockResolvedValue(mockSessionData as any);

    const { fetchSessionDetails, messages, currentSession } = useChatSession();
    
    await fetchSessionDetails('sess-2');
    
    expect(currentSession.value).toEqual(mockSessionData);
    expect(messages.value.length).toBe(1);
    expect(messages.value[0].content).toBe('Hi');
  });

  it('3. should reconstruct steps and tools for workflow mode if messages are empty', async () => {
    const mockSessionData = {
      id: 'sess-3',
      title: 'Workflow Task',
      mode: 'workflow',
      workflow_state: {
        tasks: [
          { id: 'task-1', name: 'Step 1', status: 'completed', toolCalls: [{ tool_name: 'Search', status: 'completed' }] }
        ]
      },
      messages: []
    };
    vi.mocked(chatService.getSession).mockResolvedValue(mockSessionData as any);

    const { fetchSessionDetails, messages } = useChatSession();
    
    await fetchSessionDetails('sess-3');
    
    expect(messages.value.length).toBe(2); // user msg + assistant msg
    const assistantMsg = messages.value[1];
    expect(assistantMsg.role).toBe('assistant');
    expect(assistantMsg.steps?.length).toBe(1);
    expect(assistantMsg.steps?.[0].content).toBe('Step 1');
    expect(assistantMsg.tools?.length).toBe(1);
    expect(assistantMsg.tools?.[0].name).toBe('Search');
  });

  it('4. should prevent overwriting optimistic messages during stream race condition', async () => {
    const mockSessionData = {
      id: 'sess-4',
      messages: [{ id: 'backend-msg-1', role: 'assistant', content: 'Backend response' }]
    };
    vi.mocked(chatService.getSession).mockResolvedValue(mockSessionData as any);

    const { fetchSessionDetails, messages } = useChatSession();
    messages.value = [{ role: 'user', content: 'My optimistic message', status: 'sending', timestamp: new Date().toISOString() }];
    
    // Simulate a recent stream ending for THIS session
    window._lastStreamEndTime = Date.now();
    window._lastStreamSessionId = 'sess-4';
    
    await fetchSessionDetails('sess-4');
    
    // It should skip overwriting because there's a 'sending' message
    expect(messages.value.length).toBe(1);
    expect(messages.value[0].content).toBe('My optimistic message');
  });

  it('4.1 should NOT prevent overwriting if recent stream was for a DIFFERENT session', async () => {
    const mockSessionData = {
      id: 'sess-5',
      messages: [{ id: 'backend-msg-1', role: 'assistant', content: 'Backend response' }]
    };
    vi.mocked(chatService.getSession).mockResolvedValue(mockSessionData as any);

    const { fetchSessionDetails, messages } = useChatSession();
    messages.value = []; // empty state as if we just switched sessions
    
    // Simulate a recent stream ending for a DIFFERENT session
    window._lastStreamEndTime = Date.now();
    window._lastStreamSessionId = 'some-other-session';
    
    await fetchSessionDetails('sess-5');
    
    // It SHOULD overwrite/merge because the recent stream wasn't for this session
    expect(messages.value.length).toBe(1);
    expect(messages.value[0].content).toBe('Backend response');
  });

  it('5. should handle streaming response correctly', async () => {
    const { handleStreamResponse, messages, isStreaming, isLoading } = useChatSession();
    
    // Mock Response with ReadableStream
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"content": "Hello "}\n\n'));
        controller.enqueue(encoder.encode('data: {"content": "World!"}\n\n'));
        controller.close();
      }
    });
    
    const mockResponse = new Response(stream);
    
    isLoading.value = true;
    
    const updateSpy = vi.fn();
    await handleStreamResponse(mockResponse, updateSpy);
    
    expect(messages.value.length).toBe(1);
    expect(messages.value[0].role).toBe('assistant');
    expect(messages.value[0].content).toBe('Hello World!');
    expect(isStreaming.value).toBe(false);
    expect(isLoading.value).toBe(false);
    expect(updateSpy).toHaveBeenCalled();
  });

  it('6. should stop generation', async () => {
    const { stopGeneration, isStopping, abortController } = useChatSession();
    
    abortController.value = new AbortController();
    const abortSpy = vi.spyOn(abortController.value, 'abort');
    
    stopGeneration();
    
    expect(isStopping.value).toBe(true);
    expect(abortSpy).toHaveBeenCalled();
    expect(abortController.value).toBeNull();
  });
});
