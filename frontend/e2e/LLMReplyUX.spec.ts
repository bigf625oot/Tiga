import { test, expect } from '@playwright/test';

test.describe('LLM Reply UI/UX Evaluation', () => {
  const sessionId = 'test-session-ui';
  const agentId = 'test-agent-ui';

  test.use({ viewport: { width: 1280, height: 720 } });

  test.beforeEach(async ({ page }) => {
    // 拦截会话列表 API
    await page.route('**/api/v1/chat/sessions', async route => {
        if (route.request().method() === 'GET') {
            await route.fulfill({
                json: [{ id: sessionId, title: 'UI Test', updated_at: new Date().toISOString(), agent_id: agentId, mode: 'chat' }]
            });
        } else {
            await route.continue();
        }
    });

    // 拦截会话详情 API，注入各种类型的 Mock 消息
    await page.route(`**/api/v1/chat/sessions/${sessionId}`, async route => {
      const messages = [];
      const baseTime = new Date();
      
      // 1. 用户提问
      messages.push({
        role: 'user',
        content: '请帮我搜索关于量子的知识，并查询数据库，最后总结。',
        timestamp: baseTime.toISOString()
      });

      // 2. 带有完整过程的 AI 回复
      messages.push({
        role: 'assistant',
        content: '根据查询结果，量子力学是物理学的一个分支...\n\n[DocCard: 量子力学导论](doc_123)\n\n::: file\n{"id": "file_456", "name": "data.csv", "size": 1024}\n:::',
        timestamp: baseTime.toISOString(),
        // 模拟 reasoning (Thought)
        reasoning: '首先我需要搜索量子力学，然后查询相关数据。',
        // 模拟 plan_steps
        steps: [
            { content: 'Step 1: Search the web for quantum mechanics' },
            { content: 'Step 2: Query the database for related data' }
        ],
        // 模拟 tool 调用
        tools: [
            { id: 't1', name: 'web_search', args: { query: '量子力学' }, status: 'success', result: 'Found 10 results' },
            { id: 't2', name: 'db_query', args: { sql: 'SELECT * FROM physics' }, status: 'running' }
        ],
        // 模拟引用
        sources: [
            { id: 'doc_123', title: '量子物理基础.pdf' },
            { id: 'web_001', title: '维基百科：量子' }
        ]
      });

      await route.fulfill({
        json: {
          id: sessionId,
          title: 'UI Test',
          messages: messages,
          agent_id: agentId,
          mode: 'chat',
          updated_at: new Date().toISOString()
        }
      });
    });

    await page.route('**/api/v1/agents/', async route => {
      await route.fulfill({ json: [{ id: agentId, name: 'Test Agent', icon: 'agent_1.svg' }] });
    });

    await page.goto(`/?session_id=${sessionId}`);
    await page.waitForTimeout(1000);
  });

  test('should render thought process block correctly', async ({ page }) => {
    // 检查 Thought Block 是否存在
    const thoughtBlock = page.locator('.thinking-block');
    await expect(thoughtBlock).toBeVisible();
    
    // 检查是否包含正确的文本 (TRAE 风格的文本)
    await expect(thoughtBlock).toContainText('Thought');
    
    // 展开/折叠功能测试
    const triggerBtn = thoughtBlock.locator('button').first();
    await triggerBtn.click();
    await page.waitForTimeout(300);
    // 内容应该不可见或改变状态
  });

  test('should render plan steps correctly', async ({ page }) => {
    // 检查 Plan Steps 是否存在 (寻找包含 Plan Steps 的文本或图标)
    const planStepsBtn = page.getByRole('button', { name: /Plan Steps/i });
    await expect(planStepsBtn).toBeVisible();
    
    // 检查具体的步骤内容
    await expect(page.getByText('Step 1: Search the web')).toBeVisible();
    await expect(page.getByText('Step 2: Query the database')).toBeVisible();
  });

  test('should render tool status correctly', async ({ page }) => {
    // 检查 ToolStatus 组件
    const toolContainer = page.locator('.tool-status-container');
    await expect(toolContainer).toBeVisible();
    
    // 检查总体状态头部
    await expect(toolContainer).toContainText('Using tools...');
    
    // 检查具体的工具列表
    await expect(toolContainer).toContainText('web_search');
    await expect(toolContainer).toContainText('db_query');
    
    // 检查参数折叠面板
    const showArgsBtn = toolContainer.getByText('Show args').first();
    await expect(showArgsBtn).toBeVisible();
  });

  test('should render content and references correctly', async ({ page }) => {
    // 检查 Markdown 正文
    await expect(page.locator('.markdown-body')).toContainText('量子力学是物理学的一个分支');
    
    // 检查底部 Sources 区域
    const sourcesArea = page.getByText('Sources');
    await expect(sourcesArea).toBeVisible();
    
    // 检查具体的引用
    await expect(page.getByText('量子物理基础.pdf')).toBeVisible();
    await expect(page.getByText('维基百科：量子')).toBeVisible();
  });

  test('should display action bar on hover', async ({ page }) => {
    // 找到 AI 消息卡片
    const agentCard = page.locator('.chat-card').nth(1); // 第一个是 user，第二个是 assistant
    
    // 找到操作栏按钮 (复制按钮)
    const copyBtn = agentCard.locator('button[title="复制"]').first();
    
    // 初始状态下由于 opacity-0 应该是不可见的 (但 Playwright 的 toBeVisible 可能受 CSS 影响，我们查 opacity)
    // 悬停在卡片上
    await agentCard.hover();
    await page.waitForTimeout(300); // 等待过渡动画
    
    // 验证按钮是否可点击
    await expect(copyBtn).toBeEnabled();
  });
});
