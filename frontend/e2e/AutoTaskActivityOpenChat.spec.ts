import { test, expect } from '@playwright/test';

test.describe('AutoTask activities', () => {
  test('click activity card should open chat session details', async ({ page }) => {
    const now = new Date().toISOString();

    await page.route('**/api/v1/chat/sessions', async (route) => {
      if (route.request().method() !== 'GET') return route.fallback();
      await route.fulfill({ json: [] });
    });

    await page.route('**/api/v1/agents**', async (route) => {
      await route.fulfill({ json: [] });
    });

    await page.route('**/api/v1/teams**', async (route) => {
      await route.fulfill({ json: [] });
    });

    await page.route('**/api/v1/openclaw/activities**', async (route) => {
      await route.fulfill({
        json: [
          {
            id: 'task-1',
            name: 'Task-1',
            type: 'crawl',
            status: 'DISPATCHED',
            last_run: now,
            description: '统计一下系统里有多少个用户',
            session_id: 'sess-1',
          },
        ],
      });
    });

    await page.route('**/api/v1/openclaw/stats**', async (route) => {
      await route.fulfill({ json: [] });
    });

    await page.route('**/api/v1/nodes/**', async (route) => {
      await route.fulfill({ json: [] });
    });

    await page.route('**/api/v1/chat/sessions/sess-1', async (route) => {
      await route.fulfill({
        json: {
          id: 'sess-1',
          title: '统计一下系统里有多少个用户',
          agent_id: null,
          mode: 'auto_task',
          workflow_state: null,
          created_at: now,
          updated_at: now,
          messages: [
            { id: 1, role: 'user', content: '统计一下系统里有多少个用户', message_type: 'text', meta_data: null, created_at: now },
            { id: 2, role: 'assistant', content: '任务已创建：task-1', message_type: 'text', meta_data: null, created_at: now },
          ],
        },
      });
    });

    await page.goto('/');

    await page.getByText('Openclaw', { exact: true }).click();
    await expect(page.getByText('控制中心')).toBeVisible();

    await page.getByRole('button', { name: '任务' }).click();

    const activityCard = page.getByText('统计一下系统里有多少个用户', { exact: true });
    await expect(activityCard).toBeVisible({ timeout: 30000 });
    await activityCard.click();

    await expect(page.getByText('任务已创建：task-1', { exact: true })).toBeVisible({ timeout: 30000 });
  });
});

