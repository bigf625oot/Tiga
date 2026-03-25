import { test, expect } from '@playwright/test';

const makePipeline = (id: number, name: string) => ({
  id,
  name,
  status: 'created',
  created_at: new Date(Date.now() - 3600_000).toISOString(),
  last_run_at: null,
  dag_config: null,
});

const makeLargeDagConfig = (count: number) => {
  const nodes = Array.from({ length: count }).map((_, i) => ({
    id: `node_${i}`,
    type: 'custom',
    position: { x: (i % 50) * 40, y: Math.floor(i / 50) * 40 },
    data: {
      label: `Node ${i}`,
      type: i % 3 === 0 ? 'source' : i % 3 === 1 ? 'transform' : 'sink',
      subType: i % 3 === 0 ? 'kafka' : i % 3 === 1 ? 'filter' : 'redis',
      config: {},
      status: 'idle',
    },
  }));
  return { nodes, edges: [] };
};

test.describe('ETL Pipeline Drag Performance', () => {
  test('should allow dragging a node after opening pipeline editor', async ({ page }) => {
    const pipelineId = 1;
    const pipelineName = '性能测试流水线';

    await page.route('**/api/v1/pathway/pipelines', async (route) => {
      if (route.request().method() !== 'GET') return route.fallback();
      await route.fulfill({ json: [makePipeline(pipelineId, pipelineName)] });
    });

    await page.route(`**/api/v1/pathway/pipelines/${pipelineId}`, async (route) => {
      if (route.request().method() !== 'GET') return route.fallback();
      await route.fulfill({
        json: {
          ...makePipeline(pipelineId, pipelineName),
          dag_config: makeLargeDagConfig(30),
        },
      });
    });

    await page.goto('/');

    await page.getByRole('button', { name: '知识中心', exact: true }).click();
    await page.getByText('ETL流水线', { exact: true }).click();
    await expect(page.getByText('ETL 流水线管理', { exact: true })).toBeVisible();

    await page.getByText(pipelineName, { exact: true }).click();

    const flow = page.locator('.etl-flow');
    await expect(flow).toBeVisible({ timeout: 30000 });

    const node = page.locator('.vue-flow__node', { hasText: 'Node 0' }).first();
    await expect(node).toBeVisible({ timeout: 30000 });

    const before = await node.boundingBox();
    expect(before).not.toBeNull();
    if (!before) return;
    const beforeTransform = await node.evaluate((el) => getComputedStyle(el).transform);
    const viewport = page.locator('.vue-flow__viewport').first();
    const beforeViewportTransform = await viewport.evaluate((el) => getComputedStyle(el).transform);

    // VueFlow nodes can be dragged from their center. 
    // Wait a little bit for rendering to stabilize
    await page.waitForTimeout(1000);
    
    // Playwright mouse drag
    await page.mouse.move(before.x + 10, before.y + 10);
    await page.mouse.down();
    // Move in small steps to simulate real drag
    await page.mouse.move(before.x + 100, before.y + 100, { steps: 5 });
    await page.mouse.up();

    await expect
      .poll(async () => {
        const after = await node.boundingBox();
        if (!after) return false;
        const dx = Math.abs(after.x - before.x);
        const dy = Math.abs(after.y - before.y);
        // If node position changed, drag was successful
        return dx > 20 || dy > 20;
      }, { timeout: 10000 })
      .toBe(true);
  });
});
