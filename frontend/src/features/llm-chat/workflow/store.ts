import { useChatModeStore } from '@/features/llm-chat/shared/composables/useChatModeStore';

export function useWorkflowModeStore() {
  return useChatModeStore('workflow');
}
