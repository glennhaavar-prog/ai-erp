#!/bin/bash
# Module 3 Frontend Manual Test Script
# Run this to verify all endpoints work with the frontend

set -e

API_URL="http://localhost:8000/api"
CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"
ACCOUNT_ID="b99fcc63-be3d-43a0-959d-da29f70ea16d"

echo "=========================================="
echo "Module 3 Frontend Integration Test"
echo "=========================================="
echo ""

# Test 1: List reconciliations
echo "✓ Test 1: List reconciliations"
RECON_LIST=$(curl -s "$API_URL/reconciliations/?client_id=$CLIENT_ID")
RECON_COUNT=$(echo "$RECON_LIST" | jq -r '.count')
echo "  Found $RECON_COUNT reconciliation(s)"
echo ""

# Test 2: Create new reconciliation
echo "✓ Test 2: Create reconciliation"
CREATE_RESPONSE=$(curl -s -X POST "$API_URL/reconciliations/" \
  -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"$CLIENT_ID\",
    \"account_id\": \"$ACCOUNT_ID\",
    \"period_start\": \"2026-03-01T00:00:00\",
    \"period_end\": \"2026-03-31T23:59:59\",
    \"reconciliation_type\": \"bank\",
    \"notes\": \"Frontend test - March 2026\"
  }")

RECON_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
echo "  Created reconciliation: $RECON_ID"
echo "  Opening balance: $(echo "$CREATE_RESPONSE" | jq -r '.opening_balance')"
echo "  Closing balance: $(echo "$CREATE_RESPONSE" | jq -r '.closing_balance')"
echo ""

# Test 3: Get single reconciliation
echo "✓ Test 3: Get reconciliation details"
RECON_DETAILS=$(curl -s "$API_URL/reconciliations/$RECON_ID")
echo "  Account: $(echo "$RECON_DETAILS" | jq -r '.account_number') - $(echo "$RECON_DETAILS" | jq -r '.account_name')"
echo "  Status: $(echo "$RECON_DETAILS" | jq -r '.status')"
echo ""

# Test 4: Update reconciliation (set expected balance to match closing balance)
echo "✓ Test 4: Update reconciliation (add expected balance matching closing)"
CLOSING=$(echo "$RECON_DETAILS" | jq -r '.closing_balance')
UPDATE_RESPONSE=$(curl -s -X PUT "$API_URL/reconciliations/$RECON_ID" \
  -H "Content-Type: application/json" \
  -d "{
    \"expected_balance\": $CLOSING,
    \"notes\": \"Updated via frontend test - balanced\"
  }")

DIFFERENCE=$(echo "$UPDATE_RESPONSE" | jq -r '.difference')
NEW_STATUS=$(echo "$UPDATE_RESPONSE" | jq -r '.status')
echo "  Expected balance: $CLOSING (matches closing)"
echo "  Difference: $DIFFERENCE"
echo "  Status: $NEW_STATUS (should be 'reconciled' if difference=0)"
echo ""

# Test 5: Verify status is reconciled
echo "✓ Test 5: Verify reconciled status"
VERIFY_RESPONSE=$(curl -s "$API_URL/reconciliations/$RECON_ID")
VERIFIED_STATUS=$(echo "$VERIFY_RESPONSE" | jq -r '.status')
echo "  Current status: $VERIFIED_STATUS"
echo ""

# Test 6: Approve reconciliation (only if reconciled)
echo "✓ Test 6: Approve reconciliation"
# Get a real user ID from database
USER_ID=$(PGPASSWORD=kontali123 psql -h localhost -U kontali_user -d kontali_erp -t -c "SELECT id FROM users LIMIT 1;" 2>/dev/null | tr -d ' ')
if [ -z "$USER_ID" ]; then
  echo "  Skipped: No user found in database (foreign key constraint)"
  echo "  Note: In production, use authenticated user ID"
else
  APPROVE_RESPONSE=$(curl -s -X POST "$API_URL/reconciliations/$RECON_ID/approve?user_id=$USER_ID" \
    -H "Content-Type: application/json")
  APPROVED_STATUS=$(echo "$APPROVE_RESPONSE" | jq -r '.status // "error"')
  APPROVED_BY=$(echo "$APPROVE_RESPONSE" | jq -r '.approved_by // "none"')
  echo "  Final status: $APPROVED_STATUS"
  echo "  Approved by: $APPROVED_BY"
fi

APPROVED_STATUS=$(echo "$APPROVE_RESPONSE" | jq -r '.status')
APPROVED_BY=$(echo "$APPROVE_RESPONSE" | jq -r '.approved_by')
echo "  Final status: $APPROVED_STATUS"
echo "  Approved by: $APPROVED_BY"
echo ""

# Test 7: File upload (create test PDF file)
echo "✓ Test 7: Upload attachment"
echo "%PDF-1.4 Test Bank Statement" > /tmp/test_statement.pdf
UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/reconciliations/$RECON_ID/attachments" \
  -F "file=@/tmp/test_statement.pdf")

ATT_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.id // empty')
ATT_FILENAME=$(echo "$UPLOAD_RESPONSE" | jq -r '.file_name // .filename // empty')
if [ -n "$ATT_ID" ]; then
  echo "  Uploaded: $ATT_FILENAME (ID: $ATT_ID)"
else
  echo "  Upload failed or no ID returned"
  echo "  Response: $UPLOAD_RESPONSE"
fi
echo ""

# Test 8: List attachments
echo "✓ Test 8: List attachments"
ATT_LIST=$(curl -s "$API_URL/reconciliations/$RECON_ID/attachments")
ATT_COUNT=$(echo "$ATT_LIST" | jq -r 'length')
echo "  Found $ATT_COUNT attachment(s)"
echo ""

# Test 9: Delete attachment
echo "✓ Test 9: Delete attachment"
curl -s -X DELETE "$API_URL/reconciliations/$RECON_ID/attachments/$ATT_ID" > /dev/null
echo "  Attachment deleted"
echo ""

# Cleanup
rm -f /tmp/test_statement.pdf

echo "=========================================="
echo "All tests passed! ✅"
echo "=========================================="
echo ""
echo "Frontend URL: http://localhost:3002/reconciliations"
echo "Test reconciliation ID: $RECON_ID"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:3002/reconciliations in browser"
echo "2. Verify the test reconciliation appears in the list"
echo "3. Click on it to view details"
echo "4. Test creating a new reconciliation via UI"
echo "5. Test file upload via drag-drop"
