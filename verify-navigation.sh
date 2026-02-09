#!/bin/bash
# Kontali Navigation Verification Script
# Run this to verify all fixes are working

echo "🧪 KONTALI NAVIGATION VERIFICATION"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if server is running
echo "TEST 1: Server Status"
if lsof -ti:3002 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Server is running on port 3002${NC}"
else
    echo -e "${RED}❌ Server is NOT running on port 3002${NC}"
    echo "   Start with: cd frontend && npm run dev"
    exit 1
fi
echo ""

# Test 2: Check if page loads
echo "TEST 2: Page Loads"
if curl -s http://localhost:3002 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Homepage is accessible${NC}"
else
    echo -e "${RED}❌ Cannot access homepage${NC}"
    exit 1
fi
echo ""

# Test 3: ViewMode Toggle Present
echo "TEST 3: ViewMode Toggle"
if curl -s http://localhost:3002 | grep -q 'title="Multi-klient visning"'; then
    echo -e "${GREEN}✅ ViewMode toggle is present${NC}"
else
    echo -e "${RED}❌ ViewMode toggle NOT found${NC}"
fi
echo ""

# Test 4: Sidebar Present
echo "TEST 4: Sidebar Navigation"
SIDEBAR_HTML=$(curl -s http://localhost:3002)
if echo "$SIDEBAR_HTML" | grep -q "Innboks"; then
    echo -e "${GREEN}✅ Sidebar menu items present${NC}"
else
    echo -e "${RED}❌ Sidebar NOT found${NC}"
fi
echo ""

# Test 5: Navigation Links
echo "TEST 5: Navigation Links"
LINK_COUNT=$(curl -s http://localhost:3002 | grep -o '<a[^>]*href="[^"]*"[^>]*>' | grep -c 'href')
if [ "$LINK_COUNT" -gt 5 ]; then
    echo -e "${GREEN}✅ Found $LINK_COUNT navigation links${NC}"
else
    echo -e "${YELLOW}⚠️  Found only $LINK_COUNT navigation links${NC}"
fi
echo ""

# Test 6: Key Routes
echo "TEST 6: Key Routes Exist"
ROUTES=("/dashboard" "/review-queue" "/bank" "/accounts" "/chat")
for route in "${ROUTES[@]}"; do
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:3002$route" | grep -q "200"; then
        echo -e "${GREEN}✅ Route $route is accessible${NC}"
    else
        echo -e "${YELLOW}⚠️  Route $route returned non-200 status${NC}"
    fi
done
echo ""

# Test 7: Check for JavaScript errors (basic)
echo "TEST 7: Page Structure"
PAGE_HTML=$(curl -s http://localhost:3002)
if echo "$PAGE_HTML" | grep -q "class=\"lucide lucide-chevron-right\""; then
    echo -e "${GREEN}✅ Expandable menu items present (chevron icons found)${NC}"
else
    echo -e "${YELLOW}⚠️  Chevron icons not found (may affect expansion)${NC}"
fi
echo ""

# Test 8: ViewMode Context
echo "TEST 8: ViewMode Buttons"
if echo "$PAGE_HTML" | grep -q "LayoutGrid" && echo "$PAGE_HTML" | grep -q "Building2"; then
    echo -e "${GREEN}✅ Both view mode buttons present (Multi & Klient)${NC}"
else
    echo -e "${RED}❌ View mode buttons incomplete${NC}"
fi
echo ""

# Summary
echo "===================================="
echo "📋 VERIFICATION COMPLETE"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3002 in your browser"
echo "2. Open browser console (F12)"
echo "3. Click sidebar menu items to test expansion"
echo "4. Click view mode toggle to test switching"
echo "5. Verify console logs show 'Toggling item: ...' messages"
echo ""
echo "For detailed testing, see: NAVIGATION_FIX_REPORT.md"
echo "For browser tests, run: node test-navigation.js (in browser console)"
