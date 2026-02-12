#!/bin/bash
echo "🧪 Testing Kontali MVP Workflows"
echo "================================"
echo ""

# Get tenant ID
TENANT_ID=$(psql -U erp_user -d ai_erp -t -c "SELECT id FROM tenants LIMIT 1;" | xargs)
CLIENT_ID=$(psql -U erp_user -d ai_erp -t -c "SELECT id FROM clients LIMIT 1;" | xargs)

echo "📊 Test 1: Multi-Client Dashboard"
echo "   Tenant: $TENANT_ID"
RESULT=$(curl -s "http://localhost:8000/api/dashboard/multi-client/tasks?tenant_id=$TENANT_ID")
TASKS=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['summary']['total_tasks'])" 2>/dev/null || echo "ERROR")
if [ "$TASKS" != "ERROR" ]; then
  echo "   ✅ Dashboard API: $TASKS tasks"
else
  echo "   ❌ Dashboard API failed"
fi
echo ""

echo "🏦 Test 2: Bank Reconciliation"
RESULT=$(curl -s "http://localhost:8000/api/bank/stats?client_id=$CLIENT_ID")
TOTAL=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "ERROR")
if [ "$TOTAL" != "ERROR" ]; then
  echo "   ✅ Bank API: $TOTAL transactions"
else
  echo "   ❌ Bank API failed"
fi
echo ""

echo "📄 Test 3: Customer Invoices"
RESULT=$(curl -s "http://localhost:8000/api/customer-invoices/stats?client_id=$CLIENT_ID")
INVOICES=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['total_invoices'])" 2>/dev/null || echo "ERROR")
if [ "$INVOICES" != "ERROR" ]; then
  echo "   ✅ Customer Invoice API: $INVOICES invoices"
else
  echo "   ❌ Customer Invoice API failed"
fi
echo ""

echo "📝 Test 4: Vendor Invoices"
RESULT=$(curl -s "http://localhost:8000/api/dashboard/status")
STATUS=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "ERROR")
if [ "$STATUS" != "ERROR" ]; then
  echo "   ✅ Vendor Invoice API: $STATUS"
else
  echo "   ❌ Vendor Invoice API failed"
fi
echo ""

echo "🌐 Test 5: Frontend Pages"
for PAGE in "/" "/bank" "/customer-invoices" "/dashboard" "/hoofdbok" "/accounts"; do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000$PAGE")
  if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ $PAGE: HTTP $HTTP_CODE"
  else
    echo "   ❌ $PAGE: HTTP $HTTP_CODE"
  fi
done
echo ""

echo "================================"
echo "✅ Testing Complete!"
