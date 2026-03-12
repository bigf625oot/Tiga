import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useChatSession } from '../useChatSession';
import { chatService } from '../../services/chatService';
import { useWorkflowStore } from '@/features/workflow/store/workflow.store';

// Mock dependencies
vi.mock('../../services/chatService', () => ({
  chatService: {
    getSession: vi.fn(),
    createSession: vi.fn(),
    updateSession: vi.fn(),
    sendChatMessage: vi.fn(),
    createAutoTask: vi.fn()
  }
}));

vi.mock('@/features/workflow/store/workflow.store', () => ({
  useWorkflowStore: vi.fn(() => ({
    initWorkflow: vi.fn(),
    resetWorkflow: vi.fn(),
    stopWorkflow: vi.fn(),
    runWorkflow: vi.fn(),
    isRunning: false
  }))
}));

vi.mock('@/components/ui/toast/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

describe('useChatSession', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { currentSessionId, messages, isLoading } = useChatSession();
    expect(currentSessionId.value).toBeNull();
    expect(messages.value).toEqual([]);
    expect(isLoading.value).toBe(false);
  });

  it('fetches session details correctly', async () => {
    const mockSession = {
      id: '123',
      title: 'Test Session',
      messages: [{ role: 'user', content: 'hello' }],
      workflow_state: { step: 'plan' }
    };
    (chatService.getSession as any).mockResolvedValue(mockSession);

    const { fetchSessionDetails, currentSession, messages } = useChatSession();
    await fetchSessionDetails('123');

    expect(chatService.getSession).toHaveBeenCalledWith('123');
    expect(currentSession.value).toEqual(mockSession);
    expect(messages.value).toHaveLength(1);
  });

  it('creates new session', async () => {
    const mockSession = { id: 'new-123', title: 'New', messages: [] };
    (chatService.createSession as any).mockResolvedValue(mockSession);

    const { createNewSession, currentSessionId } = useChatSession();
    const result = await createNewSession('New', 'agent-1', 'chat');

    expect(chatService.createSession).toHaveBeenCalledWith('New', 'agent-1', 'chat');
    expect(currentSessionId.value).toBe('new-123');
    expect(result).toEqual(mockSession);
  });

  it('stops generation correctly', async () => {
    const { stopGeneration, isStopping, isLoading } = useChatSession();
    
    // Simulate loading state
    isLoading.value = true;
    
    stopGeneration();
    
    expect(isStopping.value).toBe(true);
    // After timeout, it should reset
    await new Promise(resolve => setTimeout(resolve, 350));
    expect(isStopping.value).toBe(false);
    expect(isLoading.value).toBe(false);
  });
});
