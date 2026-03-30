import { useChatModeStore } from '@/features/llm-chat/shared/composables/useChatModeStore';

export function useSoloModeStore() {
  return useChatModeStore('solo');
}
