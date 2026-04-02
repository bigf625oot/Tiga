import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { useWorkflowStore } from '@/features/llm-chat/store/workflow/workflow.store';

export type LlmChatMode = 'quick' | 'solo' | 'team' | 'workflow';
type ModeSessionState = {
  sessionId: string | null;
  messages: any[];
  isLoading: boolean;
  isStreaming: boolean;
};

export const useLlmChatStore = defineStore('llmChat', () => {
  const mode = ref<LlmChatMode>('quick');
  const modeState = ref<Record<LlmChatMode, ModeSessionState>>({
    quick: { sessionId: null, messages: [], isLoading: false, isStreaming: false },
    solo: { sessionId: null, messages: [], isLoading: false, isStreaming: false },
    team: { sessionId: null, messages: [], isLoading: false, isStreaming: false },
    workflow: { sessionId: null, messages: [], isLoading: false, isStreaming: false },
  });

  const workflowStore = useWorkflowStore();
  const currentModeState = computed(() => modeState.value[mode.value]);
  const sessionId = computed(() => currentModeState.value.sessionId);
  const messages = computed(() => currentModeState.value.messages);
  const isLoading = computed(() => currentModeState.value.isLoading);
  const isStreaming = computed(() => currentModeState.value.isStreaming);

  const setMode = (newMode: LlmChatMode) => {
    mode.value = newMode;
  };

  const setSessionId = (targetMode: LlmChatMode, nextSessionId: string | null) => {
    modeState.value[targetMode].sessionId = nextSessionId;
  };

  const setMessages = (targetMode: LlmChatMode, nextMessages: any[]) => {
    modeState.value[targetMode].messages = nextMessages;
  };

  const setLoading = (targetMode: LlmChatMode, loading: boolean) => {
    modeState.value[targetMode].isLoading = loading;
  };

  const setStreaming = (targetMode: LlmChatMode, streaming: boolean) => {
    modeState.value[targetMode].isStreaming = streaming;
  };

  const clearModeSession = (targetMode: LlmChatMode) => {
    modeState.value[targetMode] = {
      sessionId: null,
      messages: [],
      isLoading: false,
      isStreaming: false,
    };
    if (targetMode === 'workflow') {
      workflowStore.resetWorkflow();
    }
  };

  const clearSession = () => {
    clearModeSession(mode.value);
  };

  return {
    mode,
    modeState,
    currentModeState,
    sessionId,
    messages,
    isLoading,
    isStreaming,
    setMode,
    setSessionId,
    setMessages,
    setLoading,
    setStreaming,
    clearModeSession,
    clearSession,
  };
});
