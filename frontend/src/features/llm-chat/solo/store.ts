import { computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useLlmChatStore } from '@/features/llm-chat/store/llmChatSlice';

export function useSoloModeStore() {
  const route = useRoute();
  const llmChatStore = useLlmChatStore();
  const sessionId = computed(() => route.query.session_id as string | null);

  llmChatStore.setMode('solo');

  watch(
    sessionId,
    (value) => {
      llmChatStore.setSessionId('solo', value);
    },
    { immediate: true }
  );

  return {
    sessionId,
  };
}
