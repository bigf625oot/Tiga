import type { RouteRecordRaw } from 'vue-router';

export const workflowChatRoutes: RouteRecordRaw[] = [
  {
    path: '/chat/workflow',
    name: 'ChatWorkflow',
    component: () => import('@/features/llm-chat/workflow/components/WorkflowView.vue'),
  },
];
