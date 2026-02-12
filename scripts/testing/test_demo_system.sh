#!/bin/bash

# Test Demo Environment System
# Quick verification that all components work

echo "🧪 Testing Kontali Demo Environment System"
echo "=========================================="
echo ""

API_BASE="http://localhost:8000/api"

# Test 1: Check demo status
echo "Test 1: GET /api/demo/status"
curl -s "${API_BASE}/demo/status" | python3 -m json.tool | head -20
echo ""

# Test 2: Check if demo environment exists
echo "Test 2: Verify demo environment"
STATUS=$(curl -s "${API_BASE}/demo/status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('demo_environment_exists', False))")
if [ "$STATUS" = "True" ]; then
    echo "✅ Demo environment exists"
else
    echo "❌ Demo environment not found"
    echo "Run: cd backend && python scripts/create_demo_environment.py"
    exit 1
fi
echo ""

# Test 3: Check client count
echo "Test 3: Verify demo clients"
CLIENT_COUNT=$(curl -s "${API_BASE}/demo/status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('stats', {}).get('clients', 0))")
echo "Demo clients: $CLIENT_COUNT"
if [ "$CLIENT_COUNT" -ge "15" ]; then
    echo "✅ Expected number of clients found"
else
    echo "⚠️  Only $CLIENT_COUNT clients found (expected 15)"
fi
echo ""

# Test 4: Check accounts
echo "Test 4: Verify chart of accounts"
ACCOUNT_COUNT=$(curl -s "${API_BASE}/demo/status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('stats', {}).get('chart_of_accounts', 0))")
echo "Chart of accounts: $ACCOUNT_COUNT"
if [ "$ACCOUNT_COUNT" -ge "195" ]; then
    echo "✅ Expected number of accounts found"
else
    echo "⚠️  Only $ACCOUNT_COUNT accounts found (expected 195)"
fi
echo ""

# Test 5: Check middleware
echo "Test 5: Check middleware header"
DEMO_HEADER=$(curl -s -I "${API_BASE}/demo/status" | grep -i "x-demo-environment")
if [ -n "$DEMO_HEADER" ]; then
    echo "✅ Demo environment header present: $DEMO_HEADER"
else
    echo "⚠️  Demo environment header not found (may need DEMO_MODE_ENABLED=true)"
fi
echo ""

# Summary
echo "=========================================="
echo "✅ Demo System Tests Complete"
echo ""
echo "Next steps:"
echo "1. Access demo control panel: http://localhost:3000/demo-control"
echo "2. Generate test data"
echo "3. Test AI workflows"
echo ""
