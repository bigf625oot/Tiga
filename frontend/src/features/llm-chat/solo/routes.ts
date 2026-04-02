import type { RouteRecordRaw } from 'vue-router';

export const soloChatRoutes: RouteRecordRaw[] = [
  {
    path: '/chat/solo',
    name: 'ChatSolo',
    component: () => import('@/features/llm-chat/solo/components/SoloView.vue'),
  },
];
