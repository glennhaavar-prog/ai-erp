#!/usr/bin/env node

/**
 * Test Script: Module 3 - Andre Bilag Frontend
 * Tests API integration and page functionality
 */

const API_BASE = 'http://localhost:8000';
const CLIENT_ID = '09409ccf-d23e-45e5-93b9-68add0b96277';

// ANSI color codes
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const BLUE = '\x1b[34m';
const RESET = '\x1b[0m';

function log(message, color = RESET) {
  console.log(`${color}${message}${RESET}`);
}

function pass(test) {
  log(`✓ ${test}`, GREEN);
}

function fail(test, error) {
  log(`✗ ${test}`, RED);
  log(`  Error: ${error}`, RED);
}

function info(message) {
  log(`ℹ ${message}`, BLUE);
}

async function test1_FetchPendingVouchers() {
  try {
    const response = await fetch(`${API_BASE}/api/other-vouchers/pending?client_id=${CLIENT_ID}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data.items || !Array.isArray(data.items)) {
      throw new Error('Invalid response structure');
    }
    
    pass(`Test 1: Fetch pending vouchers - Found ${data.items.length} voucher(s)`);
    
    if (data.items.length > 0) {
      const first = data.items[0];
      info(`  First item: ${first.type} - ${first.title}`);
      info(`  AI Confidence: ${Math.round(first.ai_confidence * 100)}%`);
      return first.id; // Return for next test
    }
    
    return null;
  } catch (error) {
    fail('Test 1: Fetch pending vouchers', error.message);
    return null;
  }
}

async function test2_FetchSingleVoucher(voucherId) {
  if (!voucherId) {
    log('⊘ Test 2: Skipped (no voucher ID from test 1)', YELLOW);
    return null;
  }
  
  try {
    const response = await fetch(`${API_BASE}/api/other-vouchers/${voucherId}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data.id) {
      throw new Error('Invalid voucher data');
    }
    
    pass(`Test 2: Fetch single voucher - ID: ${data.id}`);
    info(`  Type: ${data.type}`);
    info(`  Title: ${data.title}`);
    info(`  Status: ${data.status}`);
    
    return data;
  } catch (error) {
    fail('Test 2: Fetch single voucher', error.message);
    return null;
  }
}

async function test3_FilterByType() {
  try {
    const types = ['employee_expense', 'inventory_adjustment', 'manual_correction'];
    let totalFound = 0;
    
    for (const type of types) {
      const response = await fetch(
        `${API_BASE}/api/other-vouchers/pending?client_id=${CLIENT_ID}&type=${type}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status} for type ${type}`);
      }
      
      const data = await response.json();
      totalFound += data.items.length;
      
      info(`  ${type}: ${data.items.length} items`);
    }
    
    pass(`Test 3: Filter by type - Found ${totalFound} total items across all types`);
    return true;
  } catch (error) {
    fail('Test 3: Filter by type', error.message);
    return false;
  }
}

async function test4_ApproveVoucher(voucherId) {
  if (!voucherId) {
    log('⊘ Test 4: Skipped (no voucher ID)', YELLOW);
    return;
  }
  
  try {
    // Note: This will actually approve the voucher in the system
    // Comment out if you don't want to modify test data
    info('  WARNING: This will approve the voucher. Skipping actual approval...');
    log('⊘ Test 4: Approve voucher - Skipped (would modify data)', YELLOW);
    return;
    
    // Uncomment to actually test approval:
    /*
    const response = await fetch(`${API_BASE}/api/other-vouchers/${voucherId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: 'Test approval' }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || response.statusText);
    }
    
    const data = await response.json();
    pass(`Test 4: Approve voucher - Status: ${data.status}`);
    */
  } catch (error) {
    fail('Test 4: Approve voucher', error.message);
  }
}

async function test5_GetStats() {
  try {
    const response = await fetch(`${API_BASE}/api/other-vouchers/stats?client_id=${CLIENT_ID}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    pass('Test 5: Get statistics');
    info(`  Pending: ${data.pending || 0}`);
    info(`  Approved: ${data.approved || 0}`);
    info(`  Rejected: ${data.rejected || 0}`);
    
    if (data.by_type) {
      info(`  By type:`);
      Object.entries(data.by_type).forEach(([type, count]) => {
        info(`    ${type}: ${count}`);
      });
    }
    
    return true;
  } catch (error) {
    fail('Test 5: Get statistics', error.message);
    return false;
  }
}

async function test6_CheckFrontendBuild() {
  const fs = require('fs');
  const path = require('path');
  
  try {
    const buildDir = path.join(__dirname, '.next');
    
    if (!fs.existsSync(buildDir)) {
      throw new Error('.next directory not found - run npm run build first');
    }
    
    pass('Test 6: Frontend build exists');
    info(`  Build directory: ${buildDir}`);
    
    // Check if andre-bilag page was built
    const pageExists = fs.existsSync(path.join(__dirname, 'src', 'app', 'andre-bilag', 'page.tsx'));
    
    if (pageExists) {
      info(`  ✓ Andre bilag page source exists`);
    } else {
      throw new Error('Andre bilag page.tsx not found');
    }
    
    return true;
  } catch (error) {
    fail('Test 6: Check frontend build', error.message);
    return false;
  }
}

async function test7_CheckAPIClient() {
  const fs = require('fs');
  const path = require('path');
  
  try {
    const apiClientPath = path.join(__dirname, 'src', 'lib', 'api', 'other-vouchers.ts');
    
    if (!fs.existsSync(apiClientPath)) {
      throw new Error('API client not found');
    }
    
    const content = fs.readFileSync(apiClientPath, 'utf-8');
    
    // Check for required functions
    const requiredFunctions = [
      'fetchPendingOtherVouchers',
      'approveOtherVoucher',
      'rejectOtherVoucher',
      'correctOtherVoucher',
    ];
    
    const missingFunctions = requiredFunctions.filter(fn => !content.includes(fn));
    
    if (missingFunctions.length > 0) {
      throw new Error(`Missing functions: ${missingFunctions.join(', ')}`);
    }
    
    pass('Test 7: API client implementation');
    info(`  All required functions present`);
    
    return true;
  } catch (error) {
    fail('Test 7: Check API client', error.message);
    return false;
  }
}

async function runAllTests() {
  log('\n========================================', BLUE);
  log('Module 3 Frontend: Andre Bilag Tests', BLUE);
  log('========================================\n', BLUE);
  
  info('Testing backend API integration...\n');
  
  const voucherId = await test1_FetchPendingVouchers();
  await test2_FetchSingleVoucher(voucherId);
  await test3_FilterByType();
  await test4_ApproveVoucher(voucherId);
  await test5_GetStats();
  
  log('\n', RESET);
  info('Testing frontend implementation...\n');
  
  await test6_CheckFrontendBuild();
  await test7_CheckAPIClient();
  
  log('\n========================================', BLUE);
  log('Tests Complete!', BLUE);
  log('========================================\n', BLUE);
  
  log('Next steps:', YELLOW);
  log('1. Start dev server: npm run dev', RESET);
  log('2. Navigate to: http://localhost:3002/andre-bilag', RESET);
  log('3. Test the UI flows manually', RESET);
}

// Run tests
runAllTests().catch(error => {
  log(`\nFatal error: ${error.message}`, RED);
  process.exit(1);
});
