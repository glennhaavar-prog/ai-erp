#!/bin/bash
# Test ledger sync through the API

TENANT_ID="b3776033-40e5-42e2-ab7b-b1df97062d0c"
BASE_URL="http://localhost:8000"

echo "========================================"
echo "API Test: Create Journal Entry with Auto-Sync"
echo "========================================"

# Test 1: Create supplier invoice journal entry
echo ""
echo "TEST 1: Creating supplier invoice journal entry..."
echo "This should auto-create supplier_ledger entry"
echo ""

curl -X POST "${BASE_URL}/api/journal-entries/" \
  -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"${TENANT_ID}\",
    \"accounting_date\": \"2026-02-11\",
    \"voucher_series\": \"A\",
    \"description\": \"API Test - Supplier Invoice\",
    \"source_type\": \"manual\",
    \"lines\": [
      {
        \"account_number\": \"6300\",
        \"debit_amount\": 8000.00,
        \"credit_amount\": 0.00,
        \"line_description\": \"Office supplies\"
      },
      {
        \"account_number\": \"2740\",
        \"debit_amount\": 2000.00,
        \"credit_amount\": 0.00,
        \"line_description\": \"VAT\"
      },
      {
        \"account_number\": \"2400\",
        \"debit_amount\": 0.00,
        \"credit_amount\": 10000.00,
        \"line_description\": \"Supplier debt - should trigger ledger sync\"
      }
    ]
  }" | python3 -m json.tool

echo ""
echo ""

# Test 2: Create customer invoice journal entry
echo "TEST 2: Creating customer invoice journal entry..."
echo "This should auto-create customer_ledger entry"
echo ""

curl -X POST "${BASE_URL}/api/journal-entries/" \
  -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"${TENANT_ID}\",
    \"accounting_date\": \"2026-02-11\",
    \"voucher_series\": \"A\",
    \"description\": \"API Test - Customer Invoice\",
    \"source_type\": \"manual\",
    \"lines\": [
      {
        \"account_number\": \"1500\",
        \"debit_amount\": 7500.00,
        \"credit_amount\": 0.00,
        \"line_description\": \"Customer receivable - should trigger ledger sync\"
      },
      {
        \"account_number\": \"3000\",
        \"debit_amount\": 0.00,
        \"credit_amount\": 6000.00,
        \"line_description\": \"Sales revenue\"
      },
      {
        \"account_number\": \"2700\",
        \"debit_amount\": 0.00,
        \"credit_amount\": 1500.00,
        \"line_description\": \"VAT outgoing\"
      }
    ]
  }" | python3 -m json.tool

echo ""
echo "========================================"
echo "✅ API tests completed!"
echo "Check the database to verify ledger entries were created:"
echo "  SELECT * FROM supplier_ledger ORDER BY created_at DESC LIMIT 5;"
echo "  SELECT * FROM customer_ledger ORDER BY created_at DESC LIMIT 5;"
echo "========================================"
