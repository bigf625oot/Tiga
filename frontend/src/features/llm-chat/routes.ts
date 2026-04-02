import type { RouteRecordRaw } from 'vue-router';
import { quickChatRoutes } from '@/features/llm-chat/quick/routes';
import { soloChatRoutes } from '@/features/llm-chat/solo/routes';
import { teamChatRoutes } from '@/features/llm-chat/team/routes';
import { workflowChatRoutes } from '@/features/llm-chat/workflow/routes';

export const llmChatRoutes: RouteRecordRaw[] = [
  ...quickChatRoutes,
  ...soloChatRoutes,
  ...teamChatRoutes,
  ...workflowChatRoutes,
];
