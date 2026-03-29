import type { RouteRecordRaw } from 'vue-router';

export const quickChatRoutes: RouteRecordRaw[] = [
  {
    path: '/chat/quick',
    name: 'ChatQuick',
    component: () => import('@/features/llm-chat/quick/components/QuickView.vue'),
  },
];
