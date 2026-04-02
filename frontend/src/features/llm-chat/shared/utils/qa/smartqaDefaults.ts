import type { ModeType, Message } from '@/features/llm-chat/shared/types';

export function getSmartQADefaults(
  sessionId: string | null | undefined,
  messages?: Message[]
): {
  mode: ModeType;
  currentModeId: string | null;
} {
  // 需求变更：无论是否有会话/消息，默认都展示“秒懂”（auto）模式
  // 除非有特殊逻辑指定其他模式，目前统一返回 auto
  return { mode: 'auto', currentModeId: null };
}

