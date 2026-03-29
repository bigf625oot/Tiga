import { computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useLlmChatStore } from '@/features/llm-chat/store/llmChatSlice';

export function useTeamModeStore() {
  const route = useRoute();
  const llmChatStore = useLlmChatStore();
  const sessionId = computed(() => route.query.session_id as string | null);

  llmChatStore.setMode('team');

  watch(
    sessionId,
    (value) => {
      llmChatStore.setSessionId('team', value);
    },
    { immediate: true }
  );

  return {
    sessionId,
  };
}
