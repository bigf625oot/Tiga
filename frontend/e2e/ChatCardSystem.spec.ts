import { test, expect } from '@playwright/test';

test.describe('Agent Conversation Message Card System', () => {
  test.beforeEach(async ({ page }) => {
    // Wait for the app to load
    await page.goto('/');
    
    // Switch to agent sidebar tab if necessary, or just click the Demo button directly
    // The Demo button is added in agentSidebarItems
    // So we first click the agent tab
    await page.getByRole('button', { name: 'app.nav.agent', exact: false }).click().catch(() => {});
    // Wait for the sidebar item to be visible
    const demoButton = page.locator('text=消息卡片 Demo');
    await expect(demoButton).toBeVisible({ timeout: 10000 });
    await demoButton.click();
    
    // Wait for the Chat Demo view to mount
    await expect(page.locator('text=Agent Chat System')).toBeVisible({ timeout: 10000 });
  });

  test('should render Thought block and toggle content', async ({ page }) => {
    // The thought header text
    const thoughtHeader = page.locator('text=Thought process').first();
    await expect(thoughtHeader).toBeVisible();

    // Check if content is rendered
    const thoughtContent = page.locator('text=I need to create a new component');
    // Initially should be collapsed based on mock state "collapsed"
    // Wait, mock has 'collapsed', so it should be hidden
    // Let's toggle it
    await thoughtHeader.click();
    await expect(thoughtContent).toBeVisible();
  });

  test('should render Tool Status block', async ({ page }) => {
    const toolHeader = page.locator('text=Using fs_read_dir');
    await expect(toolHeader).toBeVisible();
    
    // Click to expand tool status
    await toolHeader.click();
    
    // Verify tool arguments and result are visible
    await expect(page.locator('text=Arguments')).toBeVisible();
    await expect(page.locator('text=Result')).toBeVisible();
    await expect(page.locator('text="Button.vue", "Input.vue"')).toBeVisible();
  });

  test('should render Action block with diff and handle actions', async ({ page }) => {
    const actionPath = page.locator('text=src/components/Card.vue');
    await expect(actionPath).toBeVisible();

    // Verify diff content
    await expect(page.locator('text=+++ b/src/components/Card.vue')).toBeVisible();

    // Find Apply button
    const applyButton = page.locator('button:has-text("Apply")');
    await expect(applyButton).toBeVisible();

    // Find Discard button
    const discardButton = page.locator('button:has-text("Discard")');
    await expect(discardButton).toBeVisible();

    // Click Apply
    await applyButton.click();
    
    // Button should now be Applied
    await expect(page.locator('button:has-text("Applied")')).toBeVisible();
  });

  test('should render Terminal block', async ({ page }) => {
    const terminalHeader = page.locator('text=Terminal');
    await expect(terminalHeader).toBeVisible();

    // Check terminal command and output
    await expect(page.locator('text=$')).toBeVisible();
    await expect(page.locator('text=npm run lint')).toBeVisible();
    await expect(page.locator('text=No errors found.')).toBeVisible();
  });
});
