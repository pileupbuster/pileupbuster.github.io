const { chromium } = require('playwright');

async function testResponsive() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Navigate to the local development server
  await page.goto('http://localhost:5173');
  
  // Wait for the page to load completely
  await page.waitForTimeout(3000);
  
  // Test different viewport sizes
  const sizes = [
    { width: 1400, height: 800, name: 'desktop' },
    { width: 1200, height: 800, name: '1200px' },
    { width: 900, height: 600, name: '900px' },
    { width: 600, height: 800, name: '600px' },
    { width: 400, height: 600, name: 'mobile' }
  ];
  
  for (const size of sizes) {
    console.log(`\n=== Testing ${size.name} (${size.width}x${size.height}) ===`);
    
    // Set viewport size
    await page.setViewportSize({ width: size.width, height: size.height });
    await page.waitForTimeout(2000);
    
    // Take screenshot of the active callsign section specifically
    const activeSection = await page.locator('.current-active-section');
    if (await activeSection.count() > 0) {
      await activeSection.screenshot({ 
        path: `active_section_${size.name}_${size.width}x${size.height}.png`
      });
    }
    
    // Take full page screenshot too
    await page.screenshot({ 
      path: `fullpage_${size.name}_${size.width}x${size.height}.png`,
      fullPage: false 
    });
    
    // Get computed styles for the image and text
    const imageStyle = await page.evaluate(() => {
      const img = document.querySelector('.operator-image-large');
      if (!img) return null;
      const computed = window.getComputedStyle(img);
      return {
        width: computed.width,
        height: computed.height,
        element: img.outerHTML.substring(0, 100) + '...'
      };
    });
    
    const callsignStyle = await page.evaluate(() => {
      const callsign = document.querySelector('.active-callsign');
      if (!callsign) return null;
      const computed = window.getComputedStyle(callsign);
      return {
        fontSize: computed.fontSize,
        text: callsign.textContent
      };
    });
    
    const nameStyle = await page.evaluate(() => {
      const name = document.querySelector('.active-name');
      if (!name) return null;
      const computed = window.getComputedStyle(name);
      return {
        fontSize: computed.fontSize,
        text: name.textContent
      };
    });
    
    console.log(`Image: ${imageStyle?.width} x ${imageStyle?.height}`);
    console.log(`Callsign (${callsignStyle?.text}): ${callsignStyle?.fontSize}`);
    console.log(`Name (${nameStyle?.text}): ${nameStyle?.fontSize}`);
    
    // Check if media query is active
    const mediaQuery = await page.evaluate((width) => {
      if (width <= 600) return '@media (max-width: 600px)';
      if (width <= 900) return '@media (max-width: 900px)';
      if (width <= 1200) return '@media (max-width: 1200px)';
      return 'no media query';
    }, size.width);
    
    console.log(`Expected media query: ${mediaQuery}`);
  }
  
  await browser.close();
  console.log('\n=== Screenshots saved ===');
  console.log('Check the following files:');
  console.log('- active_section_*.png - Close-up of the active callsign area');
  console.log('- fullpage_*.png - Full page screenshots');
}

testResponsive().catch(console.error);
