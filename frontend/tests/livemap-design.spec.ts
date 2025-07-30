import { test, expect } from '@playwright/test';

test.describe('LiveMap Design Comparison', () => {
  test('should match the liveMap design layout', async ({ page }) => {
    // Navigate to our React application
    await page.goto('http://localhost:5173/');
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Check main layout structure
    await expect(page.locator('.container')).toBeVisible();
    await expect(page.locator('.top-header')).toBeVisible();
    await expect(page.locator('.main-content')).toBeVisible();
    await expect(page.locator('.bottom-queue')).toBeVisible();
    
    // Check header elements
    await expect(page.locator('.logo-image')).toBeVisible();
    await expect(page.locator('.frequency-section')).toBeVisible();
    await expect(page.locator('.clock-section')).toBeVisible();
    
    // Check frequency display
    await expect(page.locator('.frequency-value')).toContainText('14,121.00');
    await expect(page.locator('.frequency-unit')).toContainText('MHz');
    
    // Check map section
    await expect(page.locator('.map-section')).toBeVisible();
    await expect(page.locator('.map-container')).toBeVisible();
    
    // Check sidebar
    await expect(page.locator('.sidebar')).toBeVisible();
    await expect(page.locator('.current-operator-section')).toBeVisible();
    await expect(page.locator('.queue-stats')).toBeVisible();
    
    // Check current operator card
    await expect(page.locator('.current-operator-card')).toBeVisible();
    await expect(page.locator('.current-operator-image')).toBeVisible();
    await expect(page.locator('.current-callsign')).toBeVisible();
    
    // Check queue stats
    await expect(page.locator('.stat-item').first()).toContainText('In Queue');
    await expect(page.locator('.stat-item').nth(1)).toContainText('Worked');
    
    // Check bottom queue bar has 4 positions
    const queueCards = page.locator('.queue-card');
    await expect(queueCards).toHaveCount(4);
    
    // Take screenshot for visual comparison
    await page.screenshot({ path: 'test-results/livemap-react.png', fullPage: true });
  });
  
  test('should have correct color scheme', async ({ page }) => {
    await page.goto('http://localhost:5173/');
    await page.waitForLoadState('domcontentloaded');
    
    // Check main background gradient
    const body = page.locator('body');
    const bodyStyles = await body.evaluate(el => getComputedStyle(el));
    expect(bodyStyles.background).toContain('linear-gradient');
    
    // Check header styling
    const header = page.locator('.top-header');
    const headerStyles = await header.evaluate(el => getComputedStyle(el));
    expect(headerStyles.backgroundColor).toContain('rgba(26, 26, 46, 0.9)');
    
    // Check frequency section has green accent
    const frequencySection = page.locator('.frequency-section');
    const freqStyles = await frequencySection.evaluate(el => getComputedStyle(el));
    expect(freqStyles.border).toContain('rgba(0, 255, 157, 0.3)');
  });
  
  test('should have responsive design', async ({ page }) => {
    // Test desktop layout
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('http://localhost:5173/');
    
    const mainContent = page.locator('.main-content');
    const mainStyles = await mainContent.evaluate(el => getComputedStyle(el));
    expect(mainStyles.flexDirection).toBe('row');
    
    // Test mobile layout
    await page.setViewportSize({ width: 768, height: 600 });
    await page.waitForTimeout(100); // Allow CSS to apply
    
    const mainStylesMobile = await mainContent.evaluate(el => getComputedStyle(el));
    expect(mainStylesMobile.flexDirection).toBe('column');
  });
  
  test('should display current time in header', async ({ page }) => {
    await page.goto('http://localhost:5173/');
    
    const clock = page.locator('.clock');
    await expect(clock).toBeVisible();
    
    // Check that clock shows time in HH:MM format
    const timeText = await clock.textContent();
    expect(timeText).toMatch(/^\d{2}:\d{2}$/);
  });
});

test.describe('Compare with Original LiveMap', () => {
  test('visual comparison with original', async ({ page }) => {
    // First, take a screenshot of our React version
    await page.goto('http://localhost:5173/');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000); // Allow map to load
    await page.screenshot({ path: 'test-results/react-version.png', fullPage: true });
    
    // Then take a screenshot of the original HTML version
    await page.goto('file:///C:/Users/DJDaithi/Documents/Source/liveMap/index.html');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000); // Allow map to load
    await page.screenshot({ path: 'test-results/original-version.png', fullPage: true });
    
    // Note: Visual comparison would be done manually or with additional tools
    console.log('Screenshots taken for manual comparison');
  });
});
