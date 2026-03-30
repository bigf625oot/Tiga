import { computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useLlmChatStore, type LlmChatMode } from '@/features/llm-chat/store/llmChatSlice';

export function useChatModeStore(mode: LlmChatMode) {
  const route = useRoute();
  const llmChatStore = useLlmChatStore();
  const sessionId = computed(() => route.query.session_id as string | null);

  llmChatStore.setMode(mode);

  watch(
    sessionId,
    (value) => {
      llmChatStore.setSessionId(mode, value);
    },
    { immediate: true }
  );

  return {
    sessionId,
  };
}
