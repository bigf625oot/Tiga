import { useChatModeStore } from '@/features/llm-chat/shared/composables/useChatModeStore';

export function useTeamModeStore() {
  return useChatModeStore('team');
}
