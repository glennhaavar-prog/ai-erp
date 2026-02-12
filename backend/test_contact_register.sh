#!/bin/bash
# Test script for KONTAKTREGISTER API
# Tests supplier and customer CRUD operations

BASE_URL="http://localhost:8000/api/contacts"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================="
echo "KONTAKTREGISTER API TEST"
echo "========================================="
echo ""

# You need to replace this with an actual client_id from your database
CLIENT_ID="00000000-0000-0000-0000-000000000001"

# Test 1: Create Supplier
echo "Test 1: Creating supplier..."
SUPPLIER_RESPONSE=$(curl -s -X POST "$BASE_URL/suppliers/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'$CLIENT_ID'",
    "company_name": "Test Supplier AS",
    "org_number": "123456789",
    "address": {
      "line1": "Testveien 123",
      "postal_code": "0123",
      "city": "Oslo"
    },
    "contact": {
      "person": "Ola Nordmann",
      "phone": "+47 12345678",
      "email": "ola@testsupplier.no"
    },
    "financial": {
      "payment_terms_days": 30,
      "currency": "NOK",
      "default_expense_account": "6300"
    }
  }')

SUPPLIER_ID=$(echo $SUPPLIER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ -n "$SUPPLIER_ID" ]; then
  echo -e "${GREEN}✓ Supplier created with ID: $SUPPLIER_ID${NC}"
else
  echo -e "${RED}✗ Failed to create supplier${NC}"
  echo $SUPPLIER_RESPONSE
  exit 1
fi
echo ""

# Test 2: Get Supplier
echo "Test 2: Getting supplier..."
GET_RESPONSE=$(curl -s "$BASE_URL/suppliers/$SUPPLIER_ID?include_balance=true")
echo $GET_RESPONSE | python3 -m json.tool
echo ""

# Test 3: List Suppliers
echo "Test 3: Listing suppliers..."
LIST_RESPONSE=$(curl -s "$BASE_URL/suppliers/?client_id=$CLIENT_ID&status=active")
echo $LIST_RESPONSE | python3 -m json.tool
echo ""

# Test 4: Update Supplier
echo "Test 4: Updating supplier..."
UPDATE_RESPONSE=$(curl -s -X PUT "$BASE_URL/suppliers/$SUPPLIER_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Updated via API test"
  }')
echo $UPDATE_RESPONSE | python3 -m json.tool
echo ""

# Test 5: Get Audit Log
echo "Test 5: Getting audit log..."
AUDIT_RESPONSE=$(curl -s "$BASE_URL/suppliers/$SUPPLIER_ID/audit-log")
echo $AUDIT_RESPONSE | python3 -m json.tool
echo ""

# Test 6: Create Customer
echo "Test 6: Creating customer..."
CUSTOMER_RESPONSE=$(curl -s -X POST "$BASE_URL/customers/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'$CLIENT_ID'",
    "is_company": true,
    "name": "Test Customer AS",
    "org_number": "987654321",
    "address": {
      "line1": "Kundeveien 456",
      "postal_code": "0456",
      "city": "Bergen"
    },
    "contact": {
      "person": "Kari Nordmann",
      "phone": "+47 87654321",
      "email": "kari@testcustomer.no"
    },
    "financial": {
      "payment_terms_days": 14,
      "currency": "NOK",
      "default_revenue_account": "3000",
      "use_kid": true,
      "kid_prefix": "100"
    }
  }')

CUSTOMER_ID=$(echo $CUSTOMER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)

if [ -n "$CUSTOMER_ID" ]; then
  echo -e "${GREEN}✓ Customer created with ID: $CUSTOMER_ID${NC}"
else
  echo -e "${RED}✗ Failed to create customer${NC}"
  echo $CUSTOMER_RESPONSE
  exit 1
fi
echo ""

# Test 7: Get Customer
echo "Test 7: Getting customer..."
GET_CUST_RESPONSE=$(curl -s "$BASE_URL/customers/$CUSTOMER_ID?include_balance=true")
echo $GET_CUST_RESPONSE | python3 -m json.tool
echo ""

# Test 8: Search Suppliers
echo "Test 8: Searching suppliers..."
SEARCH_RESPONSE=$(curl -s "$BASE_URL/suppliers/?client_id=$CLIENT_ID&search=Test")
echo $SEARCH_RESPONSE | python3 -m json.tool
echo ""

# Test 9: Deactivate Supplier
echo "Test 9: Deactivating supplier..."
DEACTIVATE_RESPONSE=$(curl -s -X DELETE "$BASE_URL/suppliers/$SUPPLIER_ID")
echo $DEACTIVATE_RESPONSE | python3 -m json.tool
echo ""

# Test 10: Verify Deactivation
echo "Test 10: Verifying deactivation..."
VERIFY_RESPONSE=$(curl -s "$BASE_URL/suppliers/$SUPPLIER_ID")
STATUS=$(echo $VERIFY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
if [ "$STATUS" = "inactive" ]; then
  echo -e "${GREEN}✓ Supplier successfully deactivated${NC}"
else
  echo -e "${RED}✗ Deactivation failed${NC}"
fi
echo ""

# Test 11: Duplicate org_number check
echo "Test 11: Testing duplicate org_number validation..."
DUPLICATE_RESPONSE=$(curl -s -X POST "$BASE_URL/suppliers/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'$CLIENT_ID'",
    "company_name": "Another Supplier",
    "org_number": "123456789"
  }')

ERROR=$(echo $DUPLICATE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', ''))" 2>/dev/null)
if [[ "$ERROR" == *"already exists"* ]]; then
  echo -e "${GREEN}✓ Duplicate validation working${NC}"
else
  echo -e "${RED}✗ Duplicate validation failed${NC}"
  echo $DUPLICATE_RESPONSE
fi
echo ""

echo "========================================="
echo "All tests completed!"
echo "========================================="
echo ""
echo "Summary:"
echo "- Supplier ID: $SUPPLIER_ID"
echo "- Customer ID: $CUSTOMER_ID"
echo ""
echo "You can now test these endpoints manually or through the frontend."
