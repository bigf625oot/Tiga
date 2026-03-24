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
        json: {
            "items": [
                {
                    "id": "task-1",
                    "name": "统计一下系统里有多少个用户",
                    "status": "DISPATCHED",
                    "description": "统计一下系统里有多少个用户",
                    "session_id": "sess-1",
                    "created_at": now,
                    "updated_at": now
                }
            ],
            "total": 1,
            "page": 1,
            "size": 10
        }
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

    await page.goto('/?mode=openclaw');

    // Wait for auto task mode to initialize
    await page.waitForTimeout(2000);
    
    // Switch to tasks tab
    // AutoTask mode might already be showing the tasks or we need to click a specific tab
    const taskTab = page.locator('text=任务').first();
    if (await taskTab.isVisible()) {
        await taskTab.click();
    }
    await page.waitForTimeout(1000);

    const activityCard = page.locator('.activity-card, [data-testid="activity-card"], .cursor-pointer').filter({ hasText: '统计一下系统里有多少个用户' }).first();
    if (await activityCard.isVisible()) {
        await activityCard.click();
    } else {
        await page.getByText('统计一下系统里有多少个用户').first().click();
    }

    await expect(page.getByText('任务已创建：task-1').first()).toBeVisible({ timeout: 5000 });
  });
});

