#!/bin/bash
# Quick Comprehensive Test for Kontali ERP
set -e

BACKEND="http://localhost:8000"
FRONTEND="http://localhost:3002"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0
TOTAL=0

test_endpoint() {
    local name="$1"
    local url="$2"
    local expected="${3:-200}"
    
    TOTAL=$((TOTAL + 1))
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$code" = "$expected" ]; then
        echo -e "${GREEN}✓${NC} $name (HTTP $code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $name (HTTP $code, expected $expected)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "=========================================="
echo "  KONTALI ERP QUICK TEST"
echo "=========================================="
echo ""

echo "[ BACKEND HEALTH ]"
test_endpoint "Health check" "$BACKEND/health"
test_endpoint "API docs" "$BACKEND/docs"
echo ""

echo "[ CORE APIs ]"
test_endpoint "Clients API" "$BACKEND/api/clients/"
test_endpoint "Invoices API" "$BACKEND/api/invoices/"
test_endpoint "Vouchers API" "$BACKEND/api/vouchers/"
test_endpoint "Accounts API" "$BACKEND/api/accounts/"
test_endpoint "Tasks API" "$BACKEND/api/tasks/"
test_endpoint "Review Queue API" "$BACKEND/api/review-queue/"
test_endpoint "Bank Transactions API" "$BACKEND/api/bank-transactions/"
echo ""

echo "[ REPORTS ]"
CLIENT_ID=$(curl -s "$BACKEND/api/clients/" | jq -r '.items[0].id' 2>/dev/null || echo "")
if [ -n "$CLIENT_ID" ]; then
    test_endpoint "Saldobalanse" "$BACKEND/api/reports/saldobalanse?client_id=$CLIENT_ID"
    test_endpoint "Balance Sheet" "$BACKEND/api/reports/balanse?client_id=$CLIENT_ID"
    test_endpoint "Income Statement" "$BACKEND/api/reports/resultat?client_id=$CLIENT_ID"
    test_endpoint "Hovedbok" "$BACKEND/api/reports/hovedbok?client_id=$CLIENT_ID"
    test_endpoint "Leverandørreskontro" "$BACKEND/api/reports/leverandorreskontro?client_id=$CLIENT_ID"
    test_endpoint "Kundereskontro" "$BACKEND/api/reports/kundereskontro?client_id=$CLIENT_ID"
fi
echo ""

echo "[ FRONTEND PAGES ]"
test_endpoint "Frontend root" "$FRONTEND/"
test_endpoint "Bank Reconciliation" "$FRONTEND/bank-reconciliation"
test_endpoint "Leverandørreskontro" "$FRONTEND/reskontro/leverandorer"
test_endpoint "Kundereskontro" "$FRONTEND/reskontro/kunder"
test_endpoint "Voucher Journal" "$FRONTEND/bilag/journal"
test_endpoint "Saldobalanse Report" "$FRONTEND/rapporter/saldobalanse"
test_endpoint "Balance Sheet" "$FRONTEND/rapporter/balanse"
test_endpoint "Hovedbok" "$FRONTEND/hovedbok"
test_endpoint "EHF Test Page" "$FRONTEND/test/ehf"
echo ""

echo "=========================================="
echo "  SUMMARY"
echo "=========================================="
echo -e "Total:  $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED test(s) failed${NC}"
    exit 1
fi
