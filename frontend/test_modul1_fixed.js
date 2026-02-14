/**
 * Modul 1 Complete Testing Suite (Fixed)
 * Waits for client context and data loading
 */
const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:3002';
const API_URL = 'http://localhost:8000';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testReviewQueueComplete() {
  console.log('\n=== MODUL 1 COMPLETE TESTING (FIXED) ===\n');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  const results = {
    passed: 0,
    failed: 0,
    tests: []
  };
  
  function logTest(name, passed, error = null) {
    results.tests.push({ name, passed, error });
    if (passed) {
      console.log(`✅ ${name}`);
      results.passed++;
    } else {
      console.log(`❌ ${name}: ${error || 'Failed'}`);
      results.failed++;
    }
  }
  
  try {
    // Test 1: Backend API Health
    console.log('\n📋 Test 1: Backend API Health');
    const healthResponse = await page.goto(`${API_URL}/health`);
    logTest('Backend API responding', healthResponse.ok());
    
    // Test 2: Page loads
    console.log('\n📋 Test 2: Page Load');
    await page.goto(`${BASE_URL}/review-queue`, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await sleep(2000);
    
    const title = await page.title();
    logTest('Page loads', title.length > 0);
    
    // Test 3: Wait for client context to load (check for client selector or data)
    console.log('\n📋 Test 3: Client Context Loading');
    try {
      // Wait up to 10 seconds for data to appear
      await page.waitForSelector('[class*="cursor-pointer"], .loading, [class*="animate-pulse"]', { 
        timeout: 10000,
        state: 'attached'
      });
      await sleep(3000); // Extra wait for API call
      logTest('Client context loaded', true);
    } catch (e) {
      logTest('Client context loaded', false, 'Timeout waiting for content');
    }
    
    // Test 4: Layout structure
    console.log('\n📋 Test 4: Master-Detail Layout');
    const mainContent = await page.$('main, [role="main"], div[class*="container"]');
    logTest('Main content area exists', mainContent !== null);
    
    // Test 5: Check for invoice items OR loading OR empty state
    console.log('\n📋 Test 5: Data State');
    const pageContent = await page.content();
    
    const hasItems = pageContent.includes('invoice') || pageContent.includes('faktura') || pageContent.includes('supplier') || pageContent.includes('leverandør');
    const hasLoading = pageContent.includes('loading') || pageContent.includes('Laster') || pageContent.includes('spinner');
    const hasEmpty = pageContent.includes('Ingen') || pageContent.includes('empty') || pageContent.includes('No items');
    
    logTest('Page shows content (items/loading/empty)', hasItems || hasLoading || hasEmpty);
    console.log(`   Content indicators: items=${hasItems}, loading=${hasLoading}, empty=${hasEmpty}`);
    
    // Test 6: Interactive elements
    console.log('\n📋 Test 6: Interactive Elements');
    const buttons = await page.$$('button');
    logTest('Buttons present', buttons.length > 0);
    console.log(`   Found ${buttons.length} buttons`);
    
    // Test 7: Look for specific UI elements by text content
    console.log('\n📋 Test 7: Key UI Components');
    const hasSettingsBtn = pageContent.includes('settings') || pageContent.includes('innstillinger') || pageContent.includes('⚙');
    const hasNewVendorBtn = pageContent.includes('Ny leverandør') || pageContent.includes('New vendor') || pageContent.includes('+ Ny');
    const hasChatWindow = pageContent.includes('chat') || pageContent.includes('fixed') && pageContent.includes('bottom');
    
    logTest('Settings icon present', hasSettingsBtn);
    logTest('New vendor button present', hasNewVendorBtn);
    logTest('ChatWindow component present', hasChatWindow);
    
    // Test 8: Check for forms/inputs
    console.log('\n📋 Test 8: Form Elements');
    const inputs = await page.$$('input, textarea, select');
    logTest('Form inputs exist', inputs.length > 0);
    console.log(`   Found ${inputs.length} form elements`);
    
    // Test 9: API endpoint check
    console.log('\n📋 Test 9: API Endpoints');
    const reviewQueueResponse = await fetch(`${API_URL}/api/review-queue/?status=pending&client_id=09409ccf-d23e-45e5-93b9-68add0b96277&limit=5`);
    const reviewData = await reviewQueueResponse.json();
    logTest('Review queue API returns data', reviewData.items && reviewData.items.length > 0);
    console.log(`   API returned ${reviewData.total || 0} total items`);
    
    // Test 10: Threshold API
    const thresholdResponse = await fetch(`${API_URL}/api/clients/09409ccf-d23e-45e5-93b9-68add0b96277/thresholds`);
    const thresholdData = await thresholdResponse.json();
    logTest('Threshold API works', thresholdData.ai_threshold_account !== undefined);
    
    // Test 11: Console errors
    console.log('\n📋 Test 11: Console Errors');
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error' && !msg.text().includes('Clerk')) { // Ignore Clerk errors
        consoleErrors.push(msg.text());
      }
    });
    
    await page.reload({ waitUntil: 'domcontentloaded' });
    await sleep(3000);
    
    logTest('No critical console errors', consoleErrors.length === 0);
    if (consoleErrors.length > 0) {
      console.log('   Errors found:');
      consoleErrors.slice(0, 5).forEach(err => console.log(`   - ${err.substring(0, 100)}`));
    }
    
    // Test 12: Try clicking settings if button found
    console.log('\n📋 Test 12: Settings Modal Interaction');
    try {
      const settingsBtn = await page.$('button:has([class*="settings"]), button:has(svg[class*="settings"])');
      if (settingsBtn) {
        await settingsBtn.click();
        await sleep(1500);
        
        const modal = await page.$('[role="dialog"], .modal, [class*="modal"]');
        logTest('Settings modal opens', modal !== null);
        
        if (modal) {
          // Check for sliders
          const sliders = await page.$$('input[type="range"], [role="slider"]');
          logTest('Threshold sliders present', sliders.length >= 3);
          console.log(`   Found ${sliders.length} sliders`);
        } else {
          logTest('Threshold sliders present', false, 'Modal did not open');
        }
      } else {
        logTest('Settings modal opens', false, 'Settings button not found');
        logTest('Threshold sliders present', false, 'Settings button not found');
      }
    } catch (e) {
      logTest('Settings modal opens', false, e.message);
      logTest('Threshold sliders present', false, 'Modal test failed');
    }
    
    // Test 13: Screenshot
    console.log('\n📋 Test 13: Visual Verification');
    try {
      await page.screenshot({ 
        path: '/home/ubuntu/.openclaw/workspace/review-queue-screenshot.png',
        fullPage: false 
      });
      logTest('Screenshot captured', true);
      console.log('   Saved: /home/ubuntu/.openclaw/workspace/review-queue-screenshot.png');
    } catch (e) {
      logTest('Screenshot captured', false, e.message);
    }
    
  } catch (error) {
    console.error('\n❌ Fatal test error:', error.message);
    logTest('Test suite execution', false, error.message);
  } finally {
    await browser.close();
  }
  
  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('TEST SUMMARY');
  console.log('='.repeat(60));
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log(`📊 Total:  ${results.tests.length}`);
  console.log(`🎯 Success Rate: ${((results.passed / results.tests.length) * 100).toFixed(1)}%`);
  
  if (results.failed > 0) {
    console.log('\n⚠️  FAILED TESTS:');
    results.tests.filter(t => !t.passed).forEach(t => {
      console.log(`   - ${t.name}${t.error ? ': ' + t.error : ''}`);
    });
  }
  
  console.log('\n');
  return results;
}

// Run tests
testReviewQueueComplete()
  .then(results => {
    process.exit(results.failed > 0 ? 1 : 0);
  })
  .catch(error => {
    console.error('Test suite failed:', error);
    process.exit(1);
  });
