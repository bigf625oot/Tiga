import { useChatModeStore } from '@/features/llm-chat/shared/composables/useChatModeStore';

export function useQuickModeStore() {
  return useChatModeStore('quick');
}
