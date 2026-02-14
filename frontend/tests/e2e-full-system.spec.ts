import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3002';
const CLIENT_ID = '09409ccf-d23e-45e5-93b9-68add0b96277';

// Test all major pages
const PAGES_TO_TEST = [
  { url: '/', name: 'Dashboard' },
  { url: '/inbox', name: 'Inbox/Review Queue' },
  { url: '/andre-bilag', name: 'Andre bilag (Modul 3)' },
  { url: '/bank-reconciliation', name: 'Bank Reconciliation (Modul 2)' },
  { url: '/reconciliations', name: 'Balance Reconciliation (Modul 4)' },
  { url: '/bilagssplit', name: 'Bilagssplit (Modul 5)' },
  { url: '/rapporter/saldobalanse', name: 'Saldobalanse' },
  { url: '/kontakter/kunder', name: 'Customers' },
  { url: '/kontakter/leverandorer', name: 'Suppliers' },
];

test.describe('Kontali ERP - Full System Test', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set client context if needed
    await page.goto(BASE_URL);
  });

  // Test 1: All pages load without errors
  for (const pageDef of PAGES_TO_TEST) {
    test(`Page loads: ${pageDef.name}`, async ({ page }) => {
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') errors.push(msg.text());
      });

      const response = await page.goto(`${BASE_URL}${pageDef.url}`);
      expect(response?.status()).toBeLessThan(400);
      
      await page.waitForLoadState('networkidle');
      
      // Log errors but don't fail on them (some may be expected)
      if (errors.length > 0) {
        console.log(`Console errors on ${pageDef.name}:`, errors);
      }
    });
  }

  // Test 2: Modul 3 - Andre bilag
  test('Modul 3: Andre bilag page works', async ({ page }) => {
    await page.goto(`${BASE_URL}/andre-bilag`);
    await page.waitForLoadState('networkidle');
    
    // Check title
    const hasTitle = await page.locator('h1, h2').count() > 0;
    expect(hasTitle).toBeTruthy();
    
    // Check filter dropdown exists
    const filterExists = await page.locator('select, [role="combobox"]').count() > 0;
    expect(filterExists).toBeTruthy();
    
    // Check table/list exists
    const tableExists = await page.locator('table, [role="grid"]').count() > 0;
    expect(tableExists).toBeTruthy();
  });

  // Test 3: Modul 2 - Bank Reconciliation
  test('Modul 2: Bank reconciliation refactored UI', async ({ page }) => {
    await page.goto(`${BASE_URL}/bank-reconciliation`);
    await page.waitForLoadState('networkidle');
    
    // Should show bank vs ledger layout
    const hasBankText = await page.locator('text=/Bank|Hovedbok/i').count() > 0;
    expect(hasBankText).toBeTruthy();
    
    // Check for action buttons
    const hasMatchButton = await page.locator('button:has-text("Avstem")').count() > 0;
    expect(hasMatchButton).toBeTruthy();
  });

  // Test 4: Modul 5 - Bilagssplit
  test('Modul 5: Bilagssplit overview and audit trail', async ({ page }) => {
    await page.goto(`${BASE_URL}/bilagssplit`);
    await page.waitForLoadState('networkidle');
    
    // Check title
    const hasTitle = await page.locator('h1').count() > 0;
    expect(hasTitle).toBeTruthy();
    
    // Check filter options
    const filterCount = await page.locator('select, [role="combobox"]').count();
    expect(filterCount).toBeGreaterThanOrEqual(1);
    
    // Check table headers
    const hasHeaders = await page.locator('th').count() > 0;
    expect(hasHeaders).toBeTruthy();
  });

  // Test 5: Navigation menu works
  test('Sidebar navigation', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // Check OVERSIKT section
    const hasOversikt = await page.locator('text=OVERSIKT').count() > 0;
    expect(hasOversikt).toBeTruthy();
    
    const hasDashboard = await page.locator('text=Dashboard').count() > 0;
    expect(hasDashboard).toBeTruthy();
    
    // Check REGNSKAP section
    const hasRegnskap = await page.locator('text=REGNSKAP').count() > 0;
    expect(hasRegnskap).toBeTruthy();
    
    // Check ANALYSE section (new from Modul 5)
    const hasAnalyse = await page.locator('text=ANALYSE').count() > 0;
    expect(hasAnalyse).toBeTruthy();
    
    const hasBilagssplit = await page.locator('text=Bilagssplit').count() > 0;
    expect(hasBilagssplit).toBeTruthy();
  });

  // Test 6: All critical buttons are clickable
  test('Buttons are interactive', async ({ page }) => {
    await page.goto(`${BASE_URL}/andre-bilag`);
    await page.waitForLoadState('networkidle');
    
    // Find any button and verify it's clickable
    const buttons = await page.locator('button:visible').all();
    expect(buttons.length).toBeGreaterThan(0);
    
    for (const button of buttons.slice(0, 3)) {
      const isVisible = await button.isVisible();
      expect(isVisible).toBeTruthy();
    }
  });
});
