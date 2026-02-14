#!/bin/bash

# Test script for Reconciliations API
# Tests all 8 endpoints with curl

BASE_URL="http://localhost:8000/api"
CLIENT_ID="003c74d3-4010-4591-a05c-ebdf99b72a27"  # Test AS 9998a (has accounts)

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "Reconciliations API Test Suite"
echo "================================================"
echo ""

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
    fi
}

# Function to extract JSON field
extract_json() {
    echo "$1" | grep -o "\"$2\":[^,}]*" | cut -d':' -f2- | tr -d '"' | tr -d ' '
}

# Step 0: Get a valid account ID from chart of accounts
echo -e "${YELLOW}Step 0: Getting a valid account ID...${NC}"
ACCOUNTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/accounts/?client_id=${CLIENT_ID}")
ACCOUNT_ID=$(echo "$ACCOUNTS_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$ACCOUNT_ID" ]; then
    echo -e "${RED}Error: Could not find any accounts for client${NC}"
    exit 1
fi

echo "Using Account ID: $ACCOUNT_ID"
echo ""

# Step 1: GET list (should be empty initially or show existing)
echo -e "${YELLOW}Step 1: GET /api/reconciliations/ (list all)${NC}"
RESPONSE=$(curl -s -X GET "${BASE_URL}/reconciliations/?client_id=${CLIENT_ID}")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
COUNT=$(extract_json "$RESPONSE" "count")
echo "Found $COUNT reconciliation(s)"
print_result $? "List reconciliations"
echo ""

# Step 2: POST create reconciliation
echo -e "${YELLOW}Step 2: POST /api/reconciliations/ (create new)${NC}"
CREATE_PAYLOAD='{
  "client_id": "'$CLIENT_ID'",
  "account_id": "'$ACCOUNT_ID'",
  "period_start": "2024-01-01T00:00:00",
  "period_end": "2024-01-31T23:59:59",
  "reconciliation_type": "bank",
  "notes": "Test reconciliation for January 2024"
}'

CREATE_RESPONSE=$(curl -s -X POST "${BASE_URL}/reconciliations/" \
  -H "Content-Type: application/json" \
  -d "$CREATE_PAYLOAD")

echo "$CREATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CREATE_RESPONSE"
RECONCILIATION_ID=$(extract_json "$CREATE_RESPONSE" "id")

if [ -n "$RECONCILIATION_ID" ]; then
    print_result 0 "Create reconciliation"
    echo "Created Reconciliation ID: $RECONCILIATION_ID"
else
    print_result 1 "Create reconciliation"
    echo "Failed to create reconciliation"
    exit 1
fi
echo ""

# Step 3: GET list (should now show 1 item)
echo -e "${YELLOW}Step 3: GET /api/reconciliations/ (verify creation)${NC}"
RESPONSE=$(curl -s -X GET "${BASE_URL}/reconciliations/?client_id=${CLIENT_ID}")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
COUNT=$(extract_json "$RESPONSE" "count")
echo "Found $COUNT reconciliation(s)"
print_result $? "List reconciliations after creation"
echo ""

# Step 4: GET single reconciliation
echo -e "${YELLOW}Step 4: GET /api/reconciliations/{id} (get single)${NC}"
SINGLE_RESPONSE=$(curl -s -X GET "${BASE_URL}/reconciliations/${RECONCILIATION_ID}")
echo "$SINGLE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SINGLE_RESPONSE"
print_result $? "Get single reconciliation"
echo ""

# Step 5: PUT update reconciliation
echo -e "${YELLOW}Step 5: PUT /api/reconciliations/{id} (update)${NC}"
UPDATE_PAYLOAD='{
  "expected_balance": 50000.00,
  "notes": "Updated test reconciliation with expected balance"
}'

UPDATE_RESPONSE=$(curl -s -X PUT "${BASE_URL}/reconciliations/${RECONCILIATION_ID}" \
  -H "Content-Type: application/json" \
  -d "$UPDATE_PAYLOAD")

echo "$UPDATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPDATE_RESPONSE"
DIFFERENCE=$(extract_json "$UPDATE_RESPONSE" "difference")
echo "Calculated difference: $DIFFERENCE"
print_result $? "Update reconciliation"
echo ""

# Step 6: POST upload attachment (create a test file first)
echo -e "${YELLOW}Step 6: POST /api/reconciliations/{id}/attachments (upload file)${NC}"

# Create a test PDF file
TEST_FILE="/tmp/test_reconciliation_$(date +%s).pdf"
echo "Test reconciliation document" > "$TEST_FILE"

UPLOAD_RESPONSE=$(curl -s -X POST "${BASE_URL}/reconciliations/${RECONCILIATION_ID}/attachments" \
  -F "file=@${TEST_FILE}" \
  -F "user_id=00000000-0000-0000-0000-000000000001")

echo "$UPLOAD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPLOAD_RESPONSE"
ATTACHMENT_ID=$(extract_json "$UPLOAD_RESPONSE" "id")

if [ -n "$ATTACHMENT_ID" ]; then
    print_result 0 "Upload attachment"
    echo "Created Attachment ID: $ATTACHMENT_ID"
else
    print_result 1 "Upload attachment"
    ATTACHMENT_ID=""
fi

# Clean up test file
rm -f "$TEST_FILE"
echo ""

# Step 7: GET attachments list
echo -e "${YELLOW}Step 7: GET /api/reconciliations/{id}/attachments (list attachments)${NC}"
ATTACHMENTS_RESPONSE=$(curl -s -X GET "${BASE_URL}/reconciliations/${RECONCILIATION_ID}/attachments")
echo "$ATTACHMENTS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ATTACHMENTS_RESPONSE"
ATTACHMENTS_COUNT=$(extract_json "$ATTACHMENTS_RESPONSE" "count")
echo "Found $ATTACHMENTS_COUNT attachment(s)"
print_result $? "List attachments"
echo ""

# Step 8: POST approve reconciliation
echo -e "${YELLOW}Step 8: POST /api/reconciliations/{id}/approve (approve)${NC}"
USER_ID="00000000-0000-0000-0000-000000000001"
APPROVE_RESPONSE=$(curl -s -X POST "${BASE_URL}/reconciliations/${RECONCILIATION_ID}/approve?user_id=${USER_ID}")
echo "$APPROVE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$APPROVE_RESPONSE"
STATUS=$(extract_json "$APPROVE_RESPONSE" "status")
echo "New status: $STATUS"
print_result $? "Approve reconciliation"
echo ""

# Step 9: DELETE attachment (if we created one)
if [ -n "$ATTACHMENT_ID" ]; then
    echo -e "${YELLOW}Step 9: DELETE /api/reconciliations/{id}/attachments/{attachment_id}${NC}"
    DELETE_RESPONSE=$(curl -s -X DELETE "${BASE_URL}/reconciliations/${RECONCILIATION_ID}/attachments/${ATTACHMENT_ID}")
    echo "$DELETE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$DELETE_RESPONSE"
    print_result $? "Delete attachment"
    echo ""
fi

# Summary
echo "================================================"
echo "Test Summary"
echo "================================================"
echo "All tests completed!"
echo ""
echo "Test Data Created:"
echo "  - Client ID: $CLIENT_ID"
echo "  - Account ID: $ACCOUNT_ID"
echo "  - Reconciliation ID: $RECONCILIATION_ID"
if [ -n "$ATTACHMENT_ID" ]; then
    echo "  - Attachment ID: $ATTACHMENT_ID (deleted)"
fi
echo ""
echo "You can clean up the test data by deleting the reconciliation manually."
echo ""
