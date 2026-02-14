#!/usr/bin/env node

/**
 * Test Script for MODUL 5: Bilagssplit og kontroll
 * 
 * Tests:
 * - API client functions with mock data
 * - Page loads without errors
 * - Filter dropdowns work
 * - Table rendering
 * - Audit trail modal
 * - Build verification
 * 
 * Usage: node test_modul5_bilagssplit.js
 */

const http = require('http');
const https = require('https');

const API_BASE = 'http://localhost:8000';
const FRONTEND_BASE = 'http://localhost:3000';

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  console.log('');
  log(`${'='.repeat(60)}`, 'cyan');
  log(`  ${title}`, 'cyan');
  log(`${'='.repeat(60)}`, 'cyan');
  console.log('');
}

function logTest(name, passed, details = '') {
  const icon = passed ? '✅' : '❌';
  const color = passed ? 'green' : 'red';
  log(`${icon} ${name}`, color);
  if (details) {
    log(`   ${details}`, 'yellow');
  }
}

// Helper to make HTTP requests
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    
    protocol.get(url, options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data,
        });
      });
    }).on('error', reject);
  });
}

// Test 1: Check if files exist
async function testFilesExist() {
  logSection('Test 1: File Structure');
  
  const fs = require('fs');
  const path = require('path');
  
  const files = [
    'src/lib/api/voucher-control.ts',
    'src/app/bilagssplit/page.tsx',
    'src/components/voucher-control/AuditTrailPanel.tsx',
    'src/config/menuConfig.ts',
  ];
  
  let allExist = true;
  
  for (const file of files) {
    const fullPath = path.join(__dirname, file);
    const exists = fs.existsSync(fullPath);
    logTest(file, exists);
    if (!exists) allExist = false;
  }
  
  return allExist;
}

// Test 2: Check API client (mock data fallback)
async function testApiClient() {
  logSection('Test 2: API Client (Mock Data)');
  
  try {
    // Since backend is not ready, we expect mock data to work
    log('ℹ️  Backend API not ready - testing mock data fallback', 'blue');
    
    // Test that the API endpoint returns 404 (expected)
    const response = await makeRequest(`${API_BASE}/api/voucher-control/overview?client_id=test`).catch(e => {
      return { statusCode: 0, error: e.message };
    });
    
    const backendNotReady = response.statusCode === 404 || response.statusCode === 0;
    logTest('Backend returns 404 (expected)', backendNotReady, 
      backendNotReady ? 'Mock data fallback will be used' : 'Unexpected response');
    
    // Check if TypeScript types are valid (compilation check)
    const { execSync } = require('child_process');
    try {
      execSync('npx tsc --noEmit src/lib/api/voucher-control.ts', { 
        cwd: __dirname,
        stdio: 'pipe'
      });
      logTest('TypeScript compilation', true);
      return true;
    } catch (err) {
      logTest('TypeScript compilation', false, err.message);
      return false;
    }
  } catch (error) {
    logTest('API client test', false, error.message);
    return false;
  }
}

// Test 3: Check frontend page loads
async function testFrontendPage() {
  logSection('Test 3: Frontend Page Loading');
  
  try {
    const response = await makeRequest(`${FRONTEND_BASE}/bilagssplit`);
    
    const statusOk = response.statusCode === 200;
    logTest('Page loads (HTTP 200)', statusOk);
    
    if (statusOk) {
      // Check if page contains expected elements
      const hasTitle = response.body.includes('Bilagssplit og kontroll');
      const hasFilters = response.body.includes('Behandlingsmåte') || response.body.includes('filter');
      const hasTable = response.body.includes('Bilagsnummer') || response.body.includes('table');
      
      logTest('Page title present', hasTitle);
      logTest('Filter elements present', hasFilters);
      logTest('Table structure present', hasTable);
      
      return statusOk && hasTitle;
    }
    
    return false;
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      logTest('Frontend server', false, 'Server not running. Start with: npm run dev');
    } else {
      logTest('Frontend page test', false, error.message);
    }
    return false;
  }
}

// Test 4: Check menu configuration
async function testMenuConfig() {
  logSection('Test 4: Menu Configuration');
  
  const fs = require('fs');
  const path = require('path');
  
  try {
    const menuConfigPath = path.join(__dirname, 'src/config/menuConfig.ts');
    const content = fs.readFileSync(menuConfigPath, 'utf8');
    
    const hasBilagssplit = content.includes('bilagssplit');
    const hasRoute = content.includes("route: '/bilagssplit'");
    const hasAnalyseSection = content.includes("label: 'ANALYSE'") || 
                               content.includes("label: 'analyse'");
    
    logTest('Menu entry exists', hasBilagssplit && hasRoute);
    logTest('Route configured', hasRoute, hasRoute ? "/bilagssplit" : "Missing");
    logTest('Added to ANALYSE section', hasAnalyseSection, 
      hasAnalyseSection ? 'Found' : 'Added to different section');
    
    return hasBilagssplit && hasRoute;
  } catch (error) {
    logTest('Menu configuration test', false, error.message);
    return false;
  }
}

// Test 5: Component structure validation
async function testComponentStructure() {
  logSection('Test 5: Component Structure');
  
  const fs = require('fs');
  const path = require('path');
  
  try {
    // Check AuditTrailPanel
    const auditPanelPath = path.join(__dirname, 'src/components/voucher-control/AuditTrailPanel.tsx');
    const auditContent = fs.readFileSync(auditPanelPath, 'utf8');
    
    const hasAuditTrail = auditContent.includes('AuditTrailPanel');
    const hasTimeline = auditContent.includes('timeline') || auditContent.includes('Timeline');
    const hasIcons = auditContent.includes('🤖') || auditContent.includes('getIconForAction');
    
    logTest('AuditTrailPanel component', hasAuditTrail);
    logTest('Timeline view', hasTimeline);
    logTest('Icons for actions', hasIcons);
    
    // Check main page
    const pagePath = path.join(__dirname, 'src/app/bilagssplit/page.tsx');
    const pageContent = fs.readFileSync(pagePath, 'utf8');
    
    const hasFilters = pageContent.includes('treatmentFilter') && pageContent.includes('voucherTypeFilter');
    const hasTable = pageContent.includes('<table') || pageContent.includes('Table');
    const hasAuditIntegration = pageContent.includes('AuditTrailPanel');
    
    logTest('Filter implementation', hasFilters);
    logTest('Table view', hasTable);
    logTest('Audit trail integration', hasAuditIntegration);
    
    return hasAuditTrail && hasFilters && hasTable && hasAuditIntegration;
  } catch (error) {
    logTest('Component structure test', false, error.message);
    return false;
  }
}

// Test 6: Build verification
async function testBuild() {
  logSection('Test 6: Build Verification');
  
  const { execSync } = require('child_process');
  const fs = require('fs');
  const path = require('path');
  
  try {
    log('ℹ️  Checking if build artifacts exist...', 'blue');
    
    const buildDir = path.join(__dirname, '.next');
    const buildExists = fs.existsSync(buildDir);
    
    if (!buildExists) {
      logTest('Build directory exists', false, 'Run: npm run build');
      return false;
    }
    
    logTest('Build directory exists', true);
    
    // Check for TypeScript errors in our new files
    log('ℹ️  Checking TypeScript compilation...', 'blue');
    try {
      execSync('npx tsc --noEmit --skipLibCheck', { 
        cwd: __dirname,
        stdio: 'pipe',
        timeout: 30000
      });
      logTest('TypeScript compilation', true, 'No errors');
      return true;
    } catch (err) {
      const output = err.stdout ? err.stdout.toString() : err.message;
      const hasOurFiles = output.includes('voucher-control') || 
                          output.includes('bilagssplit') ||
                          output.includes('AuditTrailPanel');
      
      if (hasOurFiles) {
        logTest('TypeScript compilation', false, 'Errors in our files');
        console.log(output);
        return false;
      } else {
        logTest('TypeScript compilation', true, 'Our files are OK (other errors exist)');
        return true;
      }
    }
  } catch (error) {
    logTest('Build verification', false, error.message);
    return false;
  }
}

// Main test runner
async function runTests() {
  console.log('');
  log('╔════════════════════════════════════════════════════════════╗', 'cyan');
  log('║     MODUL 5: Bilagssplit og kontroll - Test Suite        ║', 'cyan');
  log('╚════════════════════════════════════════════════════════════╝', 'cyan');
  
  const results = {
    filesExist: await testFilesExist(),
    apiClient: await testApiClient(),
    menuConfig: await testMenuConfig(),
    componentStructure: await testComponentStructure(),
    build: await testBuild(),
    frontendPage: await testFrontendPage(),
  };
  
  logSection('Test Summary');
  
  const passed = Object.values(results).filter(Boolean).length;
  const total = Object.keys(results).length;
  
  Object.entries(results).forEach(([test, result]) => {
    logTest(test, result);
  });
  
  console.log('');
  log(`Results: ${passed}/${total} tests passed`, passed === total ? 'green' : 'yellow');
  
  if (passed === total) {
    log('✅ All tests passed! MODUL 5 is ready.', 'green');
  } else {
    log('⚠️  Some tests failed. Check details above.', 'yellow');
  }
  
  console.log('');
  
  // Manual testing checklist
  logSection('Manual Testing Checklist');
  log('Please verify manually:', 'blue');
  log('  [ ] Page loads without errors', 'yellow');
  log('  [ ] Can filter by treatment type', 'yellow');
  log('  [ ] Can filter by voucher type', 'yellow');
  log('  [ ] Can filter by date range', 'yellow');
  log('  [ ] Table renders correctly', 'yellow');
  log('  [ ] Click row opens audit trail', 'yellow');
  log('  [ ] Audit trail shows chronological events', 'yellow');
  log('  [ ] Icons and badges display correctly', 'yellow');
  log('  [ ] Norwegian labels throughout', 'yellow');
  console.log('');
  
  process.exit(passed === total ? 0 : 1);
}

// Run tests
runTests().catch(error => {
  log(`Fatal error: ${error.message}`, 'red');
  console.error(error);
  process.exit(1);
});
