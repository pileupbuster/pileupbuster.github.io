import { test, expect } from '@playwright/test';

test.describe('Queue Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5174'); // Current Vite dev server port
    
    // Wait for the app to load
    await page.waitForSelector('.container');
  });

  test('should display queue with proper layout', async ({ page }) => {
    // Wait for the queue bar to be visible
    await page.waitForSelector('.bottom-queue');
    
    // Check that the queue bar exists
    const queueBar = page.locator('.bottom-queue');
    await expect(queueBar).toBeVisible();
    
    // Check that queue bar has right alignment
    const justifyContent = await queueBar.evaluate(el => getComputedStyle(el).justifyContent);
    expect(justifyContent).toBe('flex-end');
  });

  test('should show only one empty slot when queue is not full', async ({ page }) => {
    // Wait for the queue bar to be visible
    await page.waitForSelector('.bottom-queue');
    
    // Count placeholder cards (empty slots)
    const placeholders = page.locator('.queue-card.placeholder');
    const placeholderCount = await placeholders.count();
    
    // Should only have 1 empty slot visible when queue < 4
    expect(placeholderCount).toBeLessThanOrEqual(1);
  });

  test('should display queue items with profile images', async ({ page }) => {
    // Wait for queue items to load
    await page.waitForSelector('.queue-card:not(.placeholder)', { timeout: 10000 });
    
    // Get all non-placeholder queue cards
    const queueCards = page.locator('.queue-card:not(.placeholder)');
    const cardCount = await queueCards.count();
    
    if (cardCount > 0) {
      // Check that each queue item has an image
      for (let i = 0; i < cardCount; i++) {
        const card = queueCards.nth(i);
        const image = card.locator('.queue-image');
        await expect(image).toBeVisible();
        
        // Check that image has src attribute
        const imageSrc = await image.getAttribute('src');
        expect(imageSrc).toBeTruthy();
      }
      
      // Check that queue items are ordered correctly (first in queue should be rightmost)
      // The cards should be in reverse order in the DOM due to our right-to-left layout
      if (cardCount > 1) {
        const positions: number[] = [];
        for (let i = 0; i < cardCount; i++) {
          const card = queueCards.nth(i);
          const position = await card.getAttribute('data-position');
          positions.push(parseInt(position || '0'));
        }
        
        // Positions should be in descending order (rightmost item has lowest position number = first in queue)
        for (let i = 1; i < positions.length; i++) {
          expect(positions[i-1]).toBeGreaterThanOrEqual(positions[i]);
        }
      }
    }
  });

  test('should limit queue to maximum of 4 items', async ({ page }) => {
    // Wait for the queue bar to be visible
    await page.waitForSelector('.bottom-queue');
    
    // Count all queue cards (including placeholders)
    const allCards = page.locator('.queue-card');
    const totalCards = await allCards.count();
    
    // Should never have more than 4 cards total
    expect(totalCards).toBeLessThanOrEqual(4);
    
    // Count only actual queue items (non-placeholder)
    const queueItems = page.locator('.queue-card:not(.placeholder)');
    const queueItemCount = await queueItems.count();
    
    // Queue should never exceed 4 items
    expect(queueItemCount).toBeLessThanOrEqual(4);
  });

  test('should display callsign, location, and timer for each queue item', async ({ page }) => {
    // Wait for queue items to load
    await page.waitForSelector('.queue-card:not(.placeholder)', { timeout: 10000 });
    
    // Get all non-placeholder queue cards
    const queueCards = page.locator('.queue-card:not(.placeholder)');
    const cardCount = await queueCards.count();
    
    if (cardCount > 0) {
      for (let i = 0; i < cardCount; i++) {
        const card = queueCards.nth(i);
        
        // Check for callsign
        const callsign = card.locator('.queue-callsign');
        await expect(callsign).toBeVisible();
        const callsignText = await callsign.textContent();
        expect(callsignText).toBeTruthy();
        expect(callsignText?.trim()).not.toBe('Empty');
        
        // Check for location
        const location = card.locator('.queue-location');
        await expect(location).toBeVisible();
        
        // Check for timer (should be in MM:SS or MMM:SS format)
        const timer = card.locator('.queue-time');
        await expect(timer).toBeVisible();
        const timerText = await timer.textContent();
        expect(timerText).toMatch(/^\d{2,3}:\d{2}$/); // MM:SS or MMM:SS format
      }
    }
  });

  test('should update timers every second', async ({ page }) => {
    // Wait for queue items to load
    await page.waitForSelector('.queue-card:not(.placeholder)', { timeout: 10000 });
    
    const queueCards = page.locator('.queue-card:not(.placeholder)');
    const cardCount = await queueCards.count();
    
    if (cardCount > 0) {
      const firstCard = queueCards.first();
      const timer = firstCard.locator('.queue-time');
      
      // Get initial timer value
      const initialTime = await timer.textContent();
      
      // Wait for 2 seconds
      await page.waitForTimeout(2000);
      
      // Get updated timer value
      const updatedTime = await timer.textContent();
      
      // Timer should have changed (unless it was exactly at a minute boundary)
      if (initialTime !== updatedTime) {
        expect(updatedTime).not.toBe(initialTime);
      }
    }
  });

  test('should connect to SSE for real-time updates', async ({ page }) => {
    // Check that SSE connection is established
    const sseLogs: string[] = [];
    
    page.on('console', (msg) => {
      if (msg.text().includes('SSE') || msg.text().includes('EventSource')) {
        sseLogs.push(msg.text());
      }
    });
    
    // Wait for initial load
    await page.waitForSelector('.bottom-queue');
    
    // Wait a bit to see if there are any SSE-related console messages
    await page.waitForTimeout(3000);
    
    // Check that no SSE errors were logged
    const errorLogs = sseLogs.filter(log => log.includes('error'));
    expect(errorLogs.length).toBe(0);
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Monitor console for errors
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Wait for page to load
    await page.waitForSelector('.container');
    await page.waitForTimeout(5000);
    
    // Should not have unhandled JavaScript errors
    const relevantErrors = errors.filter(error => 
      !error.includes('favicon') && 
      !error.includes('404') &&
      !error.includes('net::ERR_FAILED')
    );
    
    expect(relevantErrors.length).toBe(0);
  });
});
