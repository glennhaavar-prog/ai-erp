/**
 * Modul 1 Complete Testing Suite
 * Tests all flows: approve, reject, multiselect, chat, settings
 */
const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:3002';
const CLIENT_ID = '09409ccf-d23e-45e5-93b9-68add0b96277';

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testReviewQueueFlows() {
  console.log('\n=== MODUL 1 COMPLETE TESTING ===\n');
  
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
      console.log(`❌ ${name}: ${error}`);
      results.failed++;
    }
  }
  
  try {
    // Test 1: Page loads
    console.log('\n📋 Test 1: Review Queue Page Load');
    await page.goto(`${BASE_URL}/review-queue`, { waitUntil: 'networkidle', timeout: 10000 });
    await sleep(2000);
    
    const title = await page.title();
    logTest('Page loads successfully', title.length > 0);
    
    // Test 2: Master-detail layout rendered
    console.log('\n📋 Test 2: Master-Detail Layout');
    const leftPanel = await page.$('[class*="w-full"][class*="md:w-"]'); // Master list
    const rightPanel = await page.$('[class*="flex-1"]'); // Detail panel
    logTest('Left panel (master list) exists', leftPanel !== null);
    logTest('Right panel (detail view) exists', rightPanel !== null);
    
    // Test 3: Invoice items rendered
    console.log('\n📋 Test 3: Invoice Items');
    await sleep(1000);
    const invoiceItems = await page.$$('[role="button"][class*="cursor-pointer"]');
    logTest('Invoice items rendered', invoiceItems.length > 0, invoiceItems.length === 0 ? 'No items found' : null);
    console.log(`   Found ${invoiceItems.length} invoice items`);
    
    // Test 4: Confidence badges
    console.log('\n📋 Test 4: Confidence Badges (Color-coded)');
    const badges = await page.$$('[class*="bg-red-"], [class*="bg-yellow-"], [class*="bg-green-"]');
    logTest('Confidence badges present', badges.length > 0);
    
    // Test 5: Click first invoice
    console.log('\n📋 Test 5: Invoice Selection');
    if (invoiceItems.length > 0) {
      await invoiceItems[0].click();
      await sleep(1000);
      
      // Check if detail panel updated
      const detailContent = await page.$('text=/Detaljer|Details|Leverandør|Supplier/i');
      logTest('Invoice detail view loads', detailContent !== null);
    } else {
      logTest('Invoice detail view loads', false, 'No invoices to select');
    }
    
    // Test 6: Approve button exists
    console.log('\n📋 Test 6: Action Buttons');
    const approveBtn = await page.$('button:has-text("Godkjenn")');
    const correctBtn = await page.$('button:has-text("Avvis")');
    logTest('Approve button exists', approveBtn !== null);
    logTest('Correct/Reject button exists', correctBtn !== null);
    
    // Test 7: Multiselect checkbox
    console.log('\n📋 Test 7: Multiselect');
    const checkboxes = await page.$$('input[type="checkbox"]');
    logTest('Multiselect checkboxes exist', checkboxes.length > 0);
    
    // Test 8: Settings button (gear icon)
    console.log('\n📋 Test 8: Settings Button');
    const settingsBtn = await page.$('button:has-text("⚙"), button[aria-label*="settings" i], button[class*="settings"]');
    logTest('Settings gear icon button exists', settingsBtn !== null);
    
    if (settingsBtn) {
      // Test 9: Settings modal opens
      console.log('\n📋 Test 9: Settings Modal');
      await settingsBtn.click();
      await sleep(1000);
      
      const modal = await page.$('[role="dialog"], [class*="modal"]');
      logTest('Settings modal opens', modal !== null);
      
      if (modal) {
        // Test 10: Threshold sliders
        console.log('\n📋 Test 10: Threshold Sliders');
        const sliders = await page.$$('input[type="range"], [role="slider"]');
        logTest('Threshold sliders present (3 expected)', sliders.length >= 3, sliders.length < 3 ? `Only ${sliders.length} found` : null);
        
        // Close modal
        const closeBtn = await page.$('button:has-text("Avbryt"), button:has-text("Cancel"), button[aria-label*="close" i]');
        if (closeBtn) await closeBtn.click();
        await sleep(500);
      }
    }
    
    // Test 11: ChatWindow component
    console.log('\n📋 Test 11: ChatWindow');
    const chatWindow = await page.$('[class*="fixed"][class*="bottom-"], [class*="chat-window"]');
    logTest('ChatWindow component present (fixed bottom-right)', chatWindow !== null);
    
    // Test 12: Vendor shortcuts button
    console.log('\n📋 Test 12: Vendor Shortcuts');
    const newVendorBtn = await page.$('button:has-text("Ny leverandør"), button:has-text("+ Ny")');
    logTest('New vendor button exists', newVendorBtn !== null);
    
    // Test 13: Console errors
    console.log('\n📋 Test 13: Console Errors');
    const consoleLogs = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleLogs.push(msg.text());
      }
    });
    
    await page.reload({ waitUntil: 'networkidle' });
    await sleep(2000);
    
    logTest('No critical console errors', consoleLogs.length === 0, 
      consoleLogs.length > 0 ? `${consoleLogs.length} errors found` : null);
    
    if (consoleLogs.length > 0) {
      console.log('\n   Console errors:');
      consoleLogs.forEach(log => console.log(`   - ${log}`));
    }
    
    // Test 14: API endpoints responding
    console.log('\n📋 Test 14: API Health');
    const response = await page.goto(`http://localhost:8000/health`);
    logTest('Backend API healthy', response.ok());
    
  } catch (error) {
    console.error('\n❌ Fatal error during testing:', error.message);
    logTest('Testing suite execution', false, error.message);
  } finally {
    await browser.close();
  }
  
  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('TEST SUMMARY');
  console.log('='.repeat(50));
  console.log(`✅ Passed: ${results.passed}`);
  console.log(`❌ Failed: ${results.failed}`);
  console.log(`📊 Total:  ${results.tests.length}`);
  console.log(`🎯 Success Rate: ${((results.passed / results.tests.length) * 100).toFixed(1)}%`);
  
  if (results.failed > 0) {
    console.log('\n⚠️  FAILED TESTS:');
    results.tests.filter(t => !t.passed).forEach(t => {
      console.log(`   - ${t.name}: ${t.error || 'Unknown error'}`);
    });
  }
  
  console.log('\n');
  return results;
}

// Run tests
testReviewQueueFlows()
  .then(results => {
    process.exit(results.failed > 0 ? 1 : 0);
  })
  .catch(error => {
    console.error('Test suite failed:', error);
    process.exit(1);
  });
