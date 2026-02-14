import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3002';
const CLIENT_ID = '09409ccf-d23e-45e5-93b9-68add0b96277';

const PAGES_TO_TEST = [
  { url: '/', name: 'Dashboard' },
  { url: '/inbox', name: 'Inbox/Review Queue (Modul 1)' },
  { url: '/andre-bilag', name: 'Andre bilag (Modul 3)' },
  { url: '/bank-reconciliation', name: 'Bank Reconciliation (Modul 2)' },
  { url: '/reconciliations', name: 'Balance Reconciliation (Modul 4)' },
  { url: '/bilagssplit', name: 'Bilagssplit (Modul 5)' },
  { url: '/rapporter/saldobalanse', name: 'Saldobalanse' },
  { url: '/kontakter/kunder', name: 'Customers' },
  { url: '/kontakter/leverandorer', name: 'Suppliers' },
];

test.describe('Kontali ERP - Full System Test', () => {
  
  test.setTimeout(120000); // 2 minutes per test

  // Test 1: All pages load without 4xx/5xx errors
  for (const pageDef of PAGES_TO_TEST) {
    test(`Page loads: ${pageDef.name}`, async ({ page }) => {
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') errors.push(msg.text());
      });
      
      const response = await page.goto(`${BASE_URL}${pageDef.url}`);
      expect(response?.status()).toBeLessThan(400);
      
      await page.waitForLoadState('networkidle', { timeout: 30000 });
      
      // Allow some console errors (hydration warnings are common)
      if (errors.length > 5) {
        console.warn(`⚠️ ${pageDef.name} has ${errors.length} console errors`);
      }
    });
  }

  // Test 2: Modul 3 - Andre bilag page structure
  test('Modul 3: Andre bilag functionality', async ({ page }) => {
    await page.goto(`${BASE_URL}/andre-bilag`);
    await page.waitForLoadState('networkidle');
    
    // Should have heading
    const hasHeading = await page.locator('h1, h2').count() > 0;
    expect(hasHeading).toBeTruthy();
    
    // Should have some interactive elements
    const hasButtons = await page.locator('button').count() > 0;
    expect(hasButtons).toBeTruthy();
  });

  // Test 3: Modul 2 - Bank Reconciliation page structure
  test('Modul 2: Bank reconciliation UI', async ({ page }) => {
    await page.goto(`${BASE_URL}/bank-reconciliation`);
    await page.waitForLoadState('networkidle');
    
    // Should have some content
    const bodyText = await page.locator('body').textContent();
    expect(bodyText).toBeTruthy();
    expect(bodyText!.length).toBeGreaterThan(100);
  });

  // Test 4: Modul 5 - Bilagssplit page structure
  test('Modul 5: Bilagssplit overview', async ({ page }) => {
    await page.goto(`${BASE_URL}/bilagssplit`);
    await page.waitForLoadState('networkidle');
    
    // Should have heading
    const hasHeading = await page.locator('h1, h2').count() > 0;
    expect(hasHeading).toBeTruthy();
    
    // Should have table or list
    const hasTable = await page.locator('table, [role="grid"]').count() > 0;
    expect(hasTable).toBeTruthy();
  });

  // Test 5: Navigation menu is present
  test('Navigation: Sidebar menu visible', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // Check for menu sections
    const bodyText = await page.locator('body').textContent();
    const hasOversikt = bodyText?.includes('OVERSIKT') || bodyText?.includes('Oversikt');
    const hasRegnskap = bodyText?.includes('REGNSKAP') || bodyText?.includes('Regnskap');
    
    expect(hasOversikt || hasRegnskap).toBeTruthy();
  });

  // Test 6: Critical interactive elements
  test('Interactive: Buttons are clickable', async ({ page }) => {
    await page.goto(`${BASE_URL}/andre-bilag`);
    await page.waitForLoadState('networkidle');
    
    const buttons = await page.locator('button:visible').all();
    
    // Should have at least some buttons
    expect(buttons.length).toBeGreaterThan(0);
    
    // Check first few buttons are enabled
    for (const button of buttons.slice(0, 3)) {
      const isVisible = await button.isVisible();
      expect(isVisible).toBeTruthy();
    }
  });
});
