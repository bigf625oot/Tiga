import { computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useLlmChatStore } from '@/features/llm-chat/store/llmChatSlice';

export function useQuickModeStore() {
  const route = useRoute();
  const llmChatStore = useLlmChatStore();
  const sessionId = computed(() => route.query.session_id as string | null);

  llmChatStore.setMode('quick');

  watch(
    sessionId,
    (value) => {
      llmChatStore.setSessionId('quick', value);
    },
    { immediate: true }
  );

  return {
    sessionId,
  };
}
