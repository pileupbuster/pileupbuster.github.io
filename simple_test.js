const { chromium } = require('playwright');

async function simpleTest() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Navigate to the frontend
    console.log('Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded' });
    
    // Wait a bit
    await page.waitForTimeout(2000);
    
    // Check if page loaded
    const title = await page.title();
    console.log('Page title:', title);
    
    // Check if active section exists
    const activeSection = await page.locator('.current-active-section').count();
    console.log('Active sections found:', activeSection);
    
    // Take screenshot of what we actually see
    await page.screenshot({ 
      path: 'actual_page.png',
      fullPage: true 
    });
    
    console.log('Screenshot saved as actual_page.png');
    
    // Check viewport size
    const viewport = page.viewportSize();
    console.log('Viewport:', viewport);
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  await browser.close();
}

simpleTest();
