import { createRouter, createWebHistory } from 'vue-router';
import { llmChatRoutes } from '@/features/llm-chat/routes';

const routes = [...llmChatRoutes];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
