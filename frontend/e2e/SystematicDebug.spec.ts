import { test, expect } from '@playwright/test';

test.describe('Systematic Debugging Scenarios from test.md', () => {
  // 考虑到首次编译加载可能较慢，增加整体测试超时时间到 60 秒
  test.setTimeout(60000);
  test.use({ viewport: { width: 1280, height: 720 } });

  test('1. 空 Thought 返回 (EMPTY_THOUGHT) - 前端“思考过程”按钮是否自动消失', async ({ page }) => {
    await page.goto('/');
    const inputArea = page.locator('textarea').first();
    await expect(inputArea).toBeVisible({ timeout: 15000 });

    await inputArea.fill('[TEST] EMPTY_THOUGHT');
    await inputArea.press('Enter');

    const currentAgentCard = page.locator('.flex.flex-col.flex-1.min-w-0.items-start').last();
    await expect(currentAgentCard).toBeVisible({ timeout: 10000 });

    // Ensure thought is hidden
    const thinkingBlock = currentAgentCard.locator('.thinking-block');
    await expect(thinkingBlock).toBeHidden({ timeout: 5000 });
    
    // Ensure content is displayed
    const markdownBody = currentAgentCard.locator('.markdown-body');
    await expect(markdownBody).toContainText('这是没有思考过程的直接回复。', { timeout: 10000 });
  });

  test('2. SSE 消息乱序 (OUT_OF_ORDER) - 前端是否有状态机管理，能重新正确排序展示', async ({ page }) => {
    await page.goto('/');
    const inputArea = page.locator('textarea').first();
    await expect(inputArea).toBeVisible({ timeout: 15000 });

    await inputArea.fill('[TEST] OUT_OF_ORDER');
    await inputArea.press('Enter');

    const currentAgentCard = page.locator('.flex.flex-col.flex-1.min-w-0.items-start').last();
    await expect(currentAgentCard).toBeVisible({ timeout: 10000 });

    // Wait for stream to end
    const cursor = currentAgentCard.locator('.animate-pulse.bg-foreground\\/60');
    await expect(cursor).toBeHidden({ timeout: 10000 });

    // The content text should combine text chunks
    const markdownBody = currentAgentCard.locator('.markdown-body');
    await expect(markdownBody).toContainText('这是第一段正文。这是第二段正文。');

    // Tool should be visible
    const toolContainer = currentAgentCard.locator('.tool-status-container');
    await expect(toolContainer).toBeVisible();
    await expect(toolContainer).toContainText('search');
    await expect(toolContainer).toContainText('Success');
  });

  test('3. JSON 转义字符攻击 (JSON_ESCAPE) - 前端是否崩溃', async ({ page }) => {
    await page.goto('/');
    const inputArea = page.locator('textarea').first();
    await expect(inputArea).toBeVisible({ timeout: 15000 });

    await inputArea.fill('[TEST] JSON_ESCAPE');
    await inputArea.press('Enter');

    const currentAgentCard = page.locator('.flex.flex-col.flex-1.min-w-0.items-start').last();
    await expect(currentAgentCard).toBeVisible({ timeout: 10000 });

    // Wait for stream to end
    const cursor = currentAgentCard.locator('.animate-pulse.bg-foreground\\/60');
    await expect(cursor).toBeHidden({ timeout: 10000 });

    // Verify it didn't crash and text is rendered
    const markdownBody = currentAgentCard.locator('.markdown-body');
    await expect(markdownBody).toContainText('破坏性测试');
  });

  test('4. Plan 描述过长 (LONG_PLAN) - 步骤标题超过100字，前端是否折行不挤压', async ({ page }) => {
    await page.goto('/');
    const inputArea = page.locator('textarea').first();
    await expect(inputArea).toBeVisible({ timeout: 15000 });

    await inputArea.fill('[TEST] LONG_PLAN');
    await inputArea.press('Enter');

    const currentAgentCard = page.locator('.flex.flex-col.flex-1.min-w-0.items-start').last();
    await expect(currentAgentCard).toBeVisible({ timeout: 10000 });

    const planBtn = currentAgentCard.getByRole('button', { name: /Plan Steps/i });
    await expect(planBtn).toBeVisible({ timeout: 10000 });

    const stepContent = currentAgentCard.locator('.text-\\[11px\\].break-words.whitespace-pre-wrap');
    await expect(stepContent.first()).toBeVisible();
    
    // Check if it wraps properly by asserting its width isn't exploding beyond container
    const box = await stepContent.first().boundingBox();
    expect(box?.width).toBeLessThan(1200); // Should fit within screen width easily
  });

  test('5. 工具执行失败 (TOOL_ERROR) - 变红并显示错误堆栈', async ({ page }) => {
    await page.goto('/');
    const inputArea = page.locator('textarea').first();
    await expect(inputArea).toBeVisible({ timeout: 15000 });

    await inputArea.fill('[TEST] TOOL_ERROR');
    await inputArea.press('Enter');

    const currentAgentCard = page.locator('.flex.flex-col.flex-1.min-w-0.items-start').last();
    await expect(currentAgentCard).toBeVisible({ timeout: 10000 });

    // Wait for stream to end
    const cursor = currentAgentCard.locator('.animate-pulse.bg-foreground\\/60');
    await expect(cursor).toBeHidden({ timeout: 10000 });

    const toolContainer = currentAgentCard.locator('.tool-status-container');
    await expect(toolContainer).toBeVisible();

    // Check for error state text
    await expect(toolContainer).toContainText('Failed');
    
    // Check for error details in the log
    await expect(toolContainer).toContainText('ZeroDivisionError');
    await expect(toolContainer.locator('.text-destructive\\/80')).toBeVisible();
  });
  
  test('6. 快速连续提问 (Fast Abort) - 必须清理状态', async ({ page }) => {
    await page.goto('/');
    const inputArea = page.locator('textarea').first();
    await expect(inputArea).toBeVisible({ timeout: 15000 });

    // We can't perfectly simulate typing while streaming if the stream finishes too fast, 
    // but we can try to send two requests quickly
    await inputArea.fill('[TEST] OUT_OF_ORDER');
    await inputArea.press('Enter');
    
    await page.waitForTimeout(100); // Small wait
    await inputArea.fill('[TEST] EMPTY_THOUGHT');
    await inputArea.press('Enter');
    
    const messages = page.locator('.flex.flex-col.flex-1.min-w-0.items-start');
    
    // Instead of fixed timeout, use expect with timeout to wait for the final message to be rendered
    const lastMessage = messages.last();
    await expect(lastMessage.locator('.markdown-body')).toContainText('这是没有思考过程的直接回复。', { timeout: 10000 });
  });
});
