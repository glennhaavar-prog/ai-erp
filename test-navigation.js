/**
 * Test script to verify Kontali navigation functionality
 * Run in browser console on http://localhost:3002
 */

console.log('🧪 KONTALI NAVIGATION TEST SUITE');
console.log('================================\n');

// Test 1: Check if ViewMode toggle exists
console.log('TEST 1: ViewMode Toggle');
const multiButton = document.querySelector('button[title="Multi-klient visning"]');
const clientButton = document.querySelector('button[title="Enkeltklient visning"]');

if (multiButton && clientButton) {
  console.log('✅ ViewMode toggle buttons found');
  console.log('   Multi button:', multiButton);
  console.log('   Client button:', clientButton);
  
  // Test click
  console.log('   Testing Multi button click...');
  multiButton.click();
  setTimeout(() => {
    console.log('   Click executed. Check if state changed.');
  }, 100);
} else {
  console.log('❌ ViewMode toggle buttons NOT found');
}

// Test 2: Check sidebar expansion
console.log('\nTEST 2: Sidebar Expansion');
const sidebarButtons = document.querySelectorAll('aside button');
console.log(`   Found ${sidebarButtons.length} sidebar buttons`);

// Find a button with children (should have ChevronRight icon)
const parentButtons = Array.from(sidebarButtons).filter(btn => {
  return btn.querySelector('.lucide-chevron-right') || btn.querySelector('.lucide-chevron-down');
});

console.log(`   Found ${parentButtons.length} parent menu items with children`);

if (parentButtons.length > 0) {
  const testButton = parentButtons[0];
  const buttonText = testButton.textContent.trim();
  console.log(`   Testing expansion of: "${buttonText}"`);
  console.log('   Before click:', testButton.querySelector('.lucide-chevron-right') ? 'Collapsed' : 'Expanded');
  
  testButton.click();
  
  setTimeout(() => {
    console.log('   After click:', testButton.querySelector('.lucide-chevron-right') ? 'Collapsed' : 'Expanded');
    console.log('   Check console for "Toggling item:" log');
  }, 100);
} else {
  console.log('❌ No parent menu items found');
}

// Test 3: Check navigation links
console.log('\nTEST 3: Navigation Links');
const navLinks = document.querySelectorAll('aside a[href]');
console.log(`   Found ${navLinks.length} navigation links`);

navLinks.forEach((link, i) => {
  const href = link.getAttribute('href');
  const text = link.textContent.trim();
  console.log(`   ${i + 1}. ${text} → ${href}`);
});

if (navLinks.length > 0) {
  console.log('   ✅ Navigation links present');
} else {
  console.log('   ❌ No navigation links found');
}

// Test 4: Check ViewMode context
console.log('\nTEST 4: ViewMode Context');
console.log('   Current view mode should be visible in React DevTools');
console.log('   Or check the active toggle button class');

const activeToggle = document.querySelector('button.bg-primary.text-primary-foreground[title*="visning"]');
if (activeToggle) {
  const isMulti = activeToggle.getAttribute('title').includes('Multi');
  console.log(`   ✅ Active view mode: ${isMulti ? 'Multi-Client' : 'Client'}`);
} else {
  console.log('   ❌ Could not determine active view mode');
}

console.log('\n================================');
console.log('📋 SUMMARY:');
console.log('   Open browser console to see full test results');
console.log('   Click sidebar menu items to test expansion');
console.log('   Click view mode toggles to test switching');
console.log('   Check for console.log messages from components');
