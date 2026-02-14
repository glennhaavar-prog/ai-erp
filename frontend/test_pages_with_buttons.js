const playwright = require('playwright');

const pages = [
  '/',
  '/review-queue',
  '/clients',
  '/accounts',
  '/kontakter/kunder',
  '/kontakter/leverandorer',
  '/rapporter/resultat',
  '/rapporter/balanse',
  '/innstillinger',
];

const BASE_URL = 'http://localhost:3002';

async function testPageWithButtons(browser, url) {
  const page = await browser.newPage();
  const errors = [];
  const clickedButtons = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  
  page.on('pageerror', error => {
    errors.push(error.message);
  });

  try {
    await page.goto(BASE_URL + url, { 
      waitUntil: 'domcontentloaded',
      timeout: 10000 
    });
    
    await page.waitForTimeout(2000);
    
    // Find all visible buttons
    const buttons = await page.locator('button:visible').all();
    const buttonCount = buttons.length;
    
    // Click first 3 buttons (to test interactivity)
    for (let i = 0; i < Math.min(3, buttonCount); i++) {
      try {
        const button = buttons[i];
        const text = await button.textContent();
        await button.click({ timeout: 2000 });
        clickedButtons.push(text?.trim() || `Button ${i+1}`);
        await page.waitForTimeout(500);
      } catch (clickError) {
        // Some buttons might not be clickable (disabled, etc)
      }
    }
    
    await page.close();
    
    return {
      url,
      status: 'success',
      buttonCount,
      clickedButtons,
      errors: errors.slice(0, 3)
    };
  } catch (error) {
    await page.close();
    return {
      url,
      status: 'failed',
      error: error.message,
      errors
    };
  }
}

(async () => {
  console.log('=== KONTALI BUTTON TESTING ===\n');
  console.log(`Testing ${pages.length} key pages with button clicks...\n`);
  
  const browser = await playwright.chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const results = [];
  
  for (const url of pages) {
    const result = await testPageWithButtons(browser, url);
    results.push(result);
    
    if (result.status === 'success') {
      console.log(`✅ ${url}`);
      console.log(`   Buttons: ${result.buttonCount} found, ${result.clickedButtons.length} tested`);
      if (result.clickedButtons.length > 0) {
        console.log(`   Clicked: ${result.clickedButtons.join(', ')}`);
      }
      if (result.errors.length > 0) {
        console.log(`   ⚠️  ${result.errors.length} console errors`);
      }
    } else {
      console.log(`❌ ${url}`);
      console.log(`   Error: ${result.error}`);
    }
    console.log('');
  }
  
  await browser.close();
  
  console.log('=== SUMMARY ===');
  const passed = results.filter(r => r.status === 'success').length;
  const failed = results.filter(r => r.status === 'failed').length;
  const totalButtons = results.reduce((sum, r) => sum + (r.buttonCount || 0), 0);
  const totalClicked = results.reduce((sum, r) => sum + (r.clickedButtons?.length || 0), 0);
  
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`🔘 Total buttons found: ${totalButtons}`);
  console.log(`👆 Buttons clicked: ${totalClicked}`);
})();
