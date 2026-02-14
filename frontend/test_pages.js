const playwright = require('playwright');

const pages = [
  '/',
  '/aapningsbalanse',
  '/accounts',
  '/accruals',
  '/audit',
  '/bank-reconciliation',
  '/bank-reconciliation-poweroffice',
  '/bank',
  '/bilag/journal',
  '/chart-of-accounts',
  '/chat',
  '/clients',
  '/customer-invoices',
  '/demo-control',
  '/import/bankintegrasjon',
  '/import/banktransaksjoner',
  '/inbox',
  '/innstillinger',
  '/innstillinger/klienter',
  '/kontakter/kunder',
  '/kontakter/kunder/ny',
  '/kontakter/leverandorer',
  '/kontakter/leverandorer/ny',
  '/nlq',
  '/oppgaver',
  '/period-close',
  '/rapporter/balanse',
  '/rapporter/hovedbok',
  '/rapporter/resultat',
  '/rapporter/saldobalanse',
  '/reports',
  '/reskontro/kunder',
  '/reskontro/leverandorer',
  '/review-queue',
  '/settings',
  '/test/ehf',
  '/trust',
  '/upload',
  '/vat',
  '/vouchers'
];

const BASE_URL = 'http://localhost:3002';

async function testPage(browser, url) {
  const page = await browser.newPage();
  const errors = [];
  const warnings = [];
  
  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    } else if (msg.type() === 'warning') {
      warnings.push(msg.text());
    }
  });
  
  // Capture page errors
  page.on('pageerror', error => {
    errors.push(error.message);
  });

  try {
    // Navigate with timeout
    await page.goto(BASE_URL + url, { 
      waitUntil: 'domcontentloaded',
      timeout: 10000 
    });
    
    // Wait a bit for React to render
    await page.waitForTimeout(1000);
    
    // Check if page loaded
    const title = await page.title();
    
    // Count buttons and links
    const buttonCount = await page.locator('button').count();
    const linkCount = await page.locator('a').count();
    
    await page.close();
    
    return {
      url,
      status: 'success',
      title,
      buttonCount,
      linkCount,
      errors: errors.slice(0, 5), // Limit to 5 errors
      warnings: warnings.slice(0, 3)
    };
  } catch (error) {
    await page.close();
    return {
      url,
      status: 'failed',
      error: error.message,
      errors,
      warnings
    };
  }
}

(async () => {
  console.log('=== KONTALI BROWSER TESTING ===\n');
  console.log(`Testing ${pages.length} pages...\n`);
  
  const browser = await playwright.chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const results = [];
  
  for (const url of pages) {
    const result = await testPage(browser, url);
    results.push(result);
    
    if (result.status === 'success') {
      console.log(`✅ ${url}`);
      if (result.errors.length > 0) {
        console.log(`   ⚠️  ${result.errors.length} console errors`);
      }
    } else {
      console.log(`❌ ${url}`);
      console.log(`   Error: ${result.error}`);
    }
  }
  
  await browser.close();
  
  // Summary
  console.log('\n=== SUMMARY ===');
  const passed = results.filter(r => r.status === 'success').length;
  const failed = results.filter(r => r.status === 'failed').length;
  const withErrors = results.filter(r => r.status === 'success' && r.errors.length > 0).length;
  
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`⚠️  With console errors: ${withErrors}`);
  
  // Detailed errors
  if (withErrors > 0) {
    console.log('\n=== PAGES WITH ERRORS ===');
    results
      .filter(r => r.status === 'success' && r.errors.length > 0)
      .forEach(r => {
        console.log(`\n${r.url}:`);
        r.errors.forEach(e => console.log(`  - ${e}`));
      });
  }
})();
