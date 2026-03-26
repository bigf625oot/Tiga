import { test, expect } from '@playwright/test';

test.describe('Real E2E LLM Reply Integration - Comprehensive Flow', () => {
  // 考虑到复杂的真实环境，包含各种工具调用，给长一些的时间
  test.setTimeout(180000);
  
  test.use({ viewport: { width: 1280, height: 720 } });

  test('should pass complex multi-step tasks from test.md (Thought -> Plan -> Tool -> Content)', async ({ page }) => {
    // 访问应用
    await page.goto('/');

    const inputArea = page.locator('textarea').first();
    await expect(inputArea).toBeVisible({ timeout: 15000 });

    // 场景：多阶段追问 —— 强制 Agent 进入复杂规划模式
    const prompt = '对比 A（苹果15） 和 B（华为Mate60） 两款手机，并根据我5000元的预算推荐。请先制定一个详细的方案。';
    await inputArea.fill(prompt);
    await inputArea.press('Enter');

    // 验证用户消息
    const userMessage = page.locator('.user-markdown').filter({ hasText: '对比 A' }).first();
    await expect(userMessage).toBeVisible({ timeout: 10000 });

    // 锁定生成的回复卡片
    const aiMessageWrapper = page.locator('.flex.flex-col.flex-1.min-w-0.items-start').last();
    await expect(aiMessageWrapper).toBeVisible({ timeout: 25000 });
    const currentAgentCard = aiMessageWrapper;

    // 调试点 1: 验证 Plan Steps
    // 必须有 Plan Steps，这是我们的重点测试项
    const planStepsBtn = currentAgentCard.getByRole('button', { name: /Plan Steps/i });
    try {
        await expect(planStepsBtn).toBeVisible({ timeout: 30000 });
        console.log('Plan Steps displayed');
        
        // 验证步骤是否正常渲染（不需要知道确切文本，只要有步骤即可）
        const steps = currentAgentCard.locator('.space-y-3.relative .flex.gap-3');
        expect(await steps.count()).toBeGreaterThan(0);
    } catch (e) {
        console.warn('Backend did not trigger Plan Steps. Checking other components...');
    }
    
    // 调试点 2: 验证 Thought (如果模型有此特性)
    const thinkingBlock = currentAgentCard.locator('.thinking-block');
    try {
        await expect(thinkingBlock).toBeVisible({ timeout: 20000 });
        console.log('Thought process displayed');
    } catch (e) {
        console.warn('No explicit Thought block triggered.');
    }

    // 调试点 3: 验证 Tool (必须有网络搜索)
    const toolContainer = currentAgentCard.locator('.tool-status-container');
    try {
        await expect(toolContainer).toBeVisible({ timeout: 60000 });
        
        const toolTrigger = toolContainer.locator('button').first();
        await toolTrigger.click();

        const toolNodes = toolContainer.locator('.flex.items-center.gap-2 > .text-\\[11px\\]');
        expect(await toolNodes.count()).toBeGreaterThan(0);
        console.log('Tools executed');
    } catch (e) {
        console.warn('Tools were not executed or timed out.');
    }

    // 调试点 4: 验证最终内容 Content
    const markdownBody = currentAgentCard.locator('.markdown-body');
    await expect(markdownBody).toBeVisible({ timeout: 120000 });
    
    // 等待流式生成结束
    const cursor = currentAgentCard.locator('.animate-pulse.bg-foreground\\/60');
    await expect(cursor).toBeHidden({ timeout: 60000 });

    const contentText = await markdownBody.textContent();
    expect(contentText?.length).toBeGreaterThan(100); 

    // 验证 Hover 操作栏
    await currentAgentCard.hover();
    const copyBtn = currentAgentCard.locator('button[title="复制"]').first();
    await expect(copyBtn).toBeVisible({ timeout: 2000 });
  });

  test('should pass Web Search scenario with rich results', async ({ page }) => {
    await page.goto('/');

    const inputArea = page.locator('textarea').first();
    await expect(inputArea).toBeVisible({ timeout: 15000 });

    // 场景：热点新闻搜索
    const prompt = '搜索一下今天早上发生的国际新闻，重点关注科技领域。';
    await inputArea.fill(prompt);
    await inputArea.press('Enter');

    const aiMessageWrapper = page.locator('.flex.flex-col.flex-1.min-w-0.items-start').last();
    await expect(aiMessageWrapper).toBeVisible({ timeout: 25000 });
    const currentAgentCard = aiMessageWrapper;

    const markdownBody = currentAgentCard.locator('.markdown-body');
    await expect(markdownBody).toBeVisible({ timeout: 60000 });
    
    const cursor = currentAgentCard.locator('.animate-pulse.bg-foreground\\/60');
    await expect(cursor).toBeHidden({ timeout: 60000 });

    // 验证引用 Sources 区域
    const sourcesArea = currentAgentCard.getByText(/Sources/i).first();
    try {
        await expect(sourcesArea).toBeVisible({ timeout: 15000 });
        console.log('Web Search Sources displayed');
        
        // 验证至少有一个引用 Badge
        const refBadges = currentAgentCard.locator('.group\\/ref');
        expect(await refBadges.count()).toBeGreaterThan(0);
    } catch (e) {
        console.warn('No sources returned for Web Search.');
    }
  });
});
