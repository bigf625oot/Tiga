import { test, expect } from '@playwright/test';

const makePipeline = (id: number, name: string) => ({
  id,
  name,
  status: 'created',
  created_at: new Date().toISOString(),
  last_run_at: null,
  dag_config: null,
});

const makeDagConfig = () => {
  const nodes = [
    {
      id: `node_1`,
      type: 'custom',
      position: { x: 100, y: 100 },
      data: {
        label: `Source Node`,
        type: 'source',
        subType: 'kafka',
        config: {},
        status: 'idle',
      },
    },
    {
      id: `node_2`,
      type: 'custom',
      position: { x: 300, y: 100 },
      data: {
        label: `Sink Node`,
        type: 'sink',
        subType: 'postgres',
        config: {},
        status: 'idle',
      },
    }
  ];
  return { nodes, edges: [] };
};

test.describe('ETL Pipeline Runtime Metrics', () => {
  test('should display RunStatsCard with metrics when pipeline is running', async ({ page }) => {
    const pipelineId = 2;
    const pipelineName = 'Metrics Test Pipeline';

    // Mock list pipelines
    await page.route('**/api/v1/pathway/pipelines*', async (route) => {
      if (route.request().method() !== 'GET') return route.fallback();
      await route.fulfill({ json: [makePipeline(pipelineId, pipelineName)] });
    });

    // Mock get pipeline (initial state - idle)
    let isRunning = false;
    await page.route(`**/api/v1/pathway/pipelines/${pipelineId}`, async (route) => {
      if (route.request().method() !== 'GET') return route.fallback();
      
      const config = makeDagConfig();
      if (isRunning) {
        config.nodes.forEach(n => {
          n.data.status = 'running';
          n.data.metrics = { eps: 120, latency: 15.5 };
        });
      }

      await route.fulfill({
        json: {
          ...makePipeline(pipelineId, pipelineName),
          status: isRunning ? 'running' : 'stopped',
          last_run_at: isRunning ? new Date().toISOString() : null,
          dag_config: config,
        },
      });
    });

    // Mock run pipeline
    await page.route(`**/api/v1/pathway/pipelines/${pipelineId}/run`, async (route) => {
      isRunning = true;
      await route.fulfill({
        json: { pipeline_id: pipelineId, status: 'running', message: 'Pipeline started' },
      });
    });

    // Mock stop pipeline
    await page.route(`**/api/v1/pathway/pipelines/${pipelineId}/stop`, async (route) => {
      isRunning = false;
      await route.fulfill({
        json: { message: 'Pipeline stopped' },
      });
    });

    await page.goto('/');

    // Navigate to ETL pipelines
    await page.getByRole('button', { name: '知识中心', exact: true }).click();
    await page.getByText('ETL流水线', { exact: true }).click();
    await expect(page.getByText('ETL 流水线管理', { exact: true })).toBeVisible();

    // Click on our test pipeline
    await page.getByText(pipelineName, { exact: true }).click();

    // Wait for the flow canvas to be visible
    const flow = page.locator('.etl-flow');
    await expect(flow).toBeVisible({ timeout: 30000 });

    // Initially, the RunStatsCard should NOT be visible
    await expect(page.getByText('运行统计', { exact: true })).not.toBeVisible();

    // Click "运行" (Run) button
    await page.getByRole('button', { name: '运行', exact: true }).click();

    // Now the RunStatsCard should appear
    const statsCard = page.locator('.bg-card\\/90'); // the card has this class
    await expect(page.getByText('运行统计', { exact: true })).toBeVisible({ timeout: 10000 });
    
    // Check if the metrics are displayed
    await expect(page.getByText('吞吐量')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('延迟')).toBeVisible({ timeout: 10000 });
    
    // We mocked EPS to be 240 (120 per node * 2 nodes)
    await expect(page.getByText('240')).toBeVisible({ timeout: 10000 });
    // We mocked latency to be 15.5
    await expect(page.getByText('15.5')).toBeVisible({ timeout: 10000 });

    // Click "停止" (Stop) button
    await page.getByRole('button', { name: '停止', exact: true }).click();

    // The RunStatsCard should disappear
    await expect(page.getByText('运行统计', { exact: true })).not.toBeVisible({ timeout: 10000 });
  });
});
