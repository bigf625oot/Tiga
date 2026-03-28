import { InjectionKey, Ref } from 'vue';
import type { ModeType, Agent } from '../../qa/types';

export interface ChatContext {
  modeId: Ref<ModeType | string | null>;
  currentAgent: Ref<Agent | null | undefined>;
  sessionId: Ref<string | null>;
  isWorkflowRunning: Ref<boolean>;
}

// Global injection key for chat context
export const ChatContextKey: InjectionKey<ChatContext> = Symbol('ChatContext');