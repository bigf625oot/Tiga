import type { RouteRecordRaw } from 'vue-router';

export const teamChatRoutes: RouteRecordRaw[] = [
  {
    path: '/chat/team',
    name: 'ChatTeam',
    component: () => import('@/features/llm-chat/team/components/TeamView.vue'),
  },
];
