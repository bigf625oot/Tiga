import { test, expect } from '@playwright/test';

test.describe('SearchAgent', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
    
    // Navigate to Search Agent view
    // 1. Click "Agent" tab in sidebar
    const agentTab = page.getByRole('button', { name: '智能体' });
    await agentTab.click();
    
    // 2. Click "Smart Search" (智能爬取) in the list
    // The sidebar items are divs with click handlers, not standard buttons/links sometimes
    // But we can find by text
    await page.getByText('智能爬取').click();
    
    // Wait for the component to load (it's async)
    await expect(page.getByText('全网智能检索')).toBeVisible();
  });

  test('should render search interface correctly', async ({ page }) => {
    await expect(page.getByPlaceholder("输入关键词，例如：'2024年工业互联网发展趋势'")).toBeVisible();
    await expect(page.getByRole('button', { name: '立即搜索' })).toBeVisible();
  });

  test('should toggle advanced options', async ({ page }) => {
    const advancedButton = page.getByRole('button', { name: '高级筛选' });
    await advancedButton.click();
    
    await expect(page.getByText('关键词分组')).toBeVisible();
    await expect(page.getByText('时间范围')).toBeVisible();
    await expect(page.getByText('数据来源')).toBeVisible();
  });

  test('should show validation error/disabled state for empty query', async ({ page }) => {
    const searchButton = page.getByRole('button', { name: '立即搜索' });
    await expect(searchButton).toBeDisabled();
    
    const input = page.getByPlaceholder("输入关键词，例如：'2024年工业互联网发展趋势'");
    await input.fill('test');
    await expect(searchButton).toBeEnabled();
  });

  // Note: We cannot easily mock the backend in E2E without network interception
  // So we will just test the UI interactions that don't strictly require a successful backend response
  // or we can intercept the request.
  
  test('should handle search interaction', async ({ page }) => {
    // Intercept API call
    await page.route('**/api/v1/news_search/search', async route => {
      const json = {
        success: true,
        data: {
          results: [
            {
              title: 'Playwright Test Result',
              url: 'https://playwright.dev',
              content: 'This is a test result content.',
              source: 'Test Source',
              news_time: '2024-03-20',
              tier: 'global'
            }
          ]
        }
      };
      await route.fulfill({ json });
    });

    const input = page.getByPlaceholder("输入关键词，例如：'2024年工业互联网发展趋势'");
    await input.fill('Playwright');
    
    const searchButton = page.getByRole('button', { name: '立即搜索' });
    await searchButton.click();
    
    // Check loading state (might be too fast to catch, but we can try)
    // await expect(page.getByTestId('loader')).toBeVisible(); // if we had testid
    
    // Check results
    await expect(page.getByText('Playwright Test Result')).toBeVisible();
    await expect(page.getByText('This is a test result content.')).toBeVisible();
    await expect(page.getByText('全网检索')).toBeVisible();
  });

  test('should handle API error', async ({ page }) => {
    // Intercept API call with error
    await page.route('**/api/v1/news_search/search', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal Server Error' })
      });
    });

    const input = page.getByPlaceholder("输入关键词，例如：'2024年工业互联网发展趋势'");
    await input.fill('Error Test');
    
    const searchButton = page.getByRole('button', { name: '立即搜索' });
    await searchButton.click();
    
    // Expect error toast/alert - wait for the first one (Toast or Alert)
    await expect(page.getByText('Internal Server Error').first()).toBeVisible();
  });
});
