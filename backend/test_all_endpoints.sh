#!/bin/bash
# API Endpoint Verification Script
# Tests all endpoints and documents their actual behavior

API_BASE="http://localhost:8000"
CLIENT_ID="628a36eb-0697-4f1e-8a0e-63963eb7b85d"  # Nordic Tech Solutions AS
TENANT_ID="123e4567-e89b-12d3-a456-426614174000"  # Demo tenant

echo "=== AI-ERP API Endpoint Verification ==="
echo "Testing against: $API_BASE"
echo ""

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    
    echo "Testing: $name"
    echo "  URL: $method $url"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" 2>&1)
    fi
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo "  ✅ Status: $http_code - OK"
        echo "  Response preview: $(echo "$body" | jq -c 2>/dev/null | head -c 100)..."
    elif [ "$http_code" = "422" ]; then
        echo "  ⚠️  Status: $http_code - Validation Error (missing required params)"
    elif [ "$http_code" = "404" ]; then
        echo "  ❌ Status: $http_code - NOT FOUND (wrong URL!)"
    else
        echo "  ⚠️  Status: $http_code"
        echo "  Error: $(echo "$body" | head -c 200)"
    fi
    echo ""
}

echo "=== CORE ENDPOINTS ==="
test_endpoint "Health Check" "$API_BASE/health"
test_endpoint "Root" "$API_BASE/"

echo "=== DASHBOARD ENDPOINTS ==="
test_endpoint "Dashboard Summary" "$API_BASE/api/dashboard/"
test_endpoint "Dashboard Status" "$API_BASE/api/dashboard/status"
test_endpoint "Dashboard Activity" "$API_BASE/api/dashboard/activity"
test_endpoint "Dashboard Verification" "$API_BASE/api/dashboard/verification"
test_endpoint "Multi-Client Tasks" "$API_BASE/api/dashboard/multi-client/tasks?tenant_id=$TENANT_ID"

echo "=== VOUCHER ENDPOINTS ==="
test_endpoint "List Vouchers" "$API_BASE/api/vouchers/list?client_id=$CLIENT_ID"

echo "=== VOUCHER JOURNAL ENDPOINTS ==="
test_endpoint "Voucher Journal List" "$API_BASE/voucher-journal/?client_id=$CLIENT_ID"
test_endpoint "Voucher Journal Stats" "$API_BASE/voucher-journal/stats?client_id=$CLIENT_ID"
test_endpoint "Voucher Types" "$API_BASE/voucher-journal/types"

echo "=== REPORTS ENDPOINTS ==="
test_endpoint "Saldobalanse" "$API_BASE/api/reports/saldobalanse?client_id=$CLIENT_ID"
test_endpoint "Resultatregnskap" "$API_BASE/api/reports/resultat?client_id=$CLIENT_ID"
test_endpoint "Balanse" "$API_BASE/api/reports/balanse?client_id=$CLIENT_ID"
test_endpoint "Hovedbok" "$API_BASE/api/reports/hovedbok?client_id=$CLIENT_ID"

echo "=== ACCOUNTS ENDPOINTS ==="
test_endpoint "List Accounts" "$API_BASE/api/accounts/?client_id=$CLIENT_ID"

echo "=== BANK ENDPOINTS ==="
test_endpoint "Bank Transactions" "$API_BASE/api/bank/transactions?client_id=$CLIENT_ID"
test_endpoint "Bank Reconciliation Stats" "$API_BASE/api/bank/reconciliation/stats?client_id=$CLIENT_ID"

echo "=== CUSTOMER ENDPOINTS ==="
test_endpoint "List Customers" "$API_BASE/api/contacts/customers/?client_id=$CLIENT_ID"

echo "=== SUPPLIER ENDPOINTS ==="
test_endpoint "List Suppliers" "$API_BASE/api/contacts/suppliers/?client_id=$CLIENT_ID"

echo "=== REVIEW QUEUE ENDPOINTS ==="
test_endpoint "Review Queue List" "$API_BASE/api/review-queue/?client_id=$CLIENT_ID"

echo "=== CLIENT ENDPOINTS ==="
test_endpoint "List Clients" "$API_BASE/api/clients"

echo "=== JOURNAL ENTRIES ENDPOINTS ==="
test_endpoint "List Journal Entries" "$API_BASE/api/journal-entries/?client_id=$CLIENT_ID"

echo "=== BANK RECONCILIATION ENDPOINTS ==="
test_endpoint "Bank Reconciliation List" "$API_BASE/api/bank-reconciliation/?client_id=$CLIENT_ID"

echo "=== CUSTOMER LEDGER ENDPOINTS ==="
test_endpoint "Customer Ledger" "$API_BASE/api/customer-ledger/?client_id=$CLIENT_ID"

echo "=== SUPPLIER LEDGER ENDPOINTS ==="
test_endpoint "Supplier Ledger" "$API_BASE/api/supplier-ledger/?client_id=$CLIENT_ID"

echo ""
echo "=== TEST COMPLETE ==="
