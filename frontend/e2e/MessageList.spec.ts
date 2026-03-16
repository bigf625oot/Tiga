import { test, expect } from '@playwright/test';

// Note: Run `npx playwright install` before running this test to ensure browsers are installed.

test.describe('MessageList Component', () => {
  const sessionId = 'test-session-list';
  const agentId = 'test-agent-list';

  // Set a large viewport to ensure we have space for scrolling
  test.use({ viewport: { width: 1280, height: 720 } });

  test.beforeEach(async ({ page }) => {
    // Mock sessions
    await page.route('**/api/v1/chat/sessions', async route => {
        if (route.request().method() === 'GET') {
            await route.fulfill({
                json: [{ id: sessionId, title: 'List Test', updated_at: new Date().toISOString(), agent_id: agentId, mode: 'chat' }]
            });
        } else {
            await route.continue();
        }
    });

    // Mock session details
    await page.route(`**/api/v1/chat/sessions/${sessionId}`, async route => {
      const messages = [];
      const baseTime = new Date();
      
      // Group 1
      messages.push({
        role: 'user',
        content: 'Hello World',
        timestamp: baseTime.toISOString()
      });

      messages.push({
        role: 'assistant',
        content: 'Hi there!',
        timestamp: baseTime.toISOString()
      });

      // Group 2
      const laterTime = new Date(baseTime.getTime() + 20 * 60 * 1000);
      messages.push({
        role: 'user',
        content: 'Later message',
        timestamp: laterTime.toISOString()
      });
      
      // Add many messages to force scrolling
      // i=0 (user), i=1 (assistant), ... i=19 (assistant)
      for(let i=0; i<20; i++) {
          messages.push({
              role: i % 2 === 0 ? 'user' : 'assistant',
              content: `Scroll message ${i}`,
              timestamp: laterTime.toISOString()
          });
      }

      await route.fulfill({
        json: {
          id: sessionId,
          title: 'List Test',
          messages: messages,
          agent_id: agentId,
          mode: 'chat',
          updated_at: new Date().toISOString()
        }
      });
    });

    // Mock agents
    await page.route('**/api/v1/agents/', async route => {
      await route.fulfill({ json: [{ id: agentId, name: 'Test Agent', icon: 'agent_1.svg' }] });
    });

    // Start navigation
    await page.goto(`/?session_id=${sessionId}`);
    
    // Wait a bit for Vue to render the list
    await page.waitForTimeout(1000);
    
    // Just ensure at least one chat card is present (list is rendered)
    await expect(page.locator('.chat-card').first()).toBeVisible();
  });

  test('should render messages correctly', async ({ page }) => {
    // Scroll to top to ensure we can see the first messages
    const container = page.locator('.overflow-y-auto').first();
    await container.evaluate(el => el.scrollTo({ top: 0, behavior: 'instant' }));
    await page.waitForTimeout(500);

    // Now check for top messages
    // User message: .user-markdown
    await expect(page.locator('.user-markdown').getByText('Hello World')).toBeVisible();
    
    // Assistant message: .markdown-body
    await expect(page.locator('.markdown-body').getByText('Hi there!')).toBeVisible();
    
    // Later message
    await expect(page.locator('.user-markdown').getByText('Later message')).toBeVisible();
  });

  test('should group messages by time', async ({ page }) => {
    // Scroll to top to see separators
    const container = page.locator('.overflow-y-auto').first();
    await container.evaluate(el => el.scrollTo({ top: 0, behavior: 'instant' }));
    await page.waitForTimeout(500);

    const separators = page.locator('div.flex.justify-center.my-4 > span.text-\\[10px\\]');
    // Check that we have at least 2 separators visible
    expect(await separators.count()).toBeGreaterThanOrEqual(2);
    await expect(separators.first()).toBeVisible();
    await expect(separators.nth(1)).toBeVisible();
  });

  test('should scroll to bottom initially', async ({ page }) => {
    // Check if the last message is visible
    // We added a spacer, so the last visible message should be index 19
    const lastMsg = page.locator('.markdown-body').getByText('Scroll message 19');
    
    // If it's not visible, maybe we need to wait a bit more for auto-scroll?
    await expect(lastMsg).toBeVisible({ timeout: 5000 });
  });

  test('should allow scrolling up', async ({ page }) => {
    // 1. Ensure we are at bottom first (or scroll there)
    const container = page.locator('.overflow-y-auto').first();
    // Force scroll to bottom just in case auto-scroll failed (to test scroll UP capability specifically)
    await container.evaluate(el => el.scrollTop = el.scrollHeight);
    await page.waitForTimeout(500);
    
    await expect(page.locator('.markdown-body').getByText('Scroll message 19')).toBeVisible();

    // 2. Scroll up
    await container.evaluate(el => el.scrollTo({ top: 0, behavior: 'instant' }));
    
    // 3. Wait a bit
    await page.waitForTimeout(500);
    
    // 4. Verify we can see "Hello World"
    await expect(page.locator('.user-markdown').getByText('Hello World')).toBeVisible();
    
    // 5. And verify we are NOT seeing the bottom message
    const bottomMsg = page.locator('.markdown-body').getByText('Scroll message 19');
    if (await bottomMsg.count() > 0) {
        await expect(bottomMsg).not.toBeInViewport();
    }
  });
});
