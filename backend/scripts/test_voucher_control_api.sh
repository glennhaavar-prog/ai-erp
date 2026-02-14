#!/bin/bash
# Test script for Voucher Control API (Modul 5 Backend)

set -e

CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"
BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Voucher Control API Test Suite"
echo "=========================================="
echo ""

# Test 1: GET overview (all)
echo "Test 1: GET overview (all vouchers)"
echo "-----------------------------------"
curl -s "$BASE_URL/api/voucher-control/overview?client_id=$CLIENT_ID" | jq '.'
echo ""
echo ""

# Test 2: GET overview (filter: auto_approved)
echo "Test 2: GET overview (filter: auto_approved)"
echo "-----------------------------------"
curl -s "$BASE_URL/api/voucher-control/overview?client_id=$CLIENT_ID&filter=auto_approved" | jq '.'
echo ""
echo ""

# Test 3: GET overview (filter: pending)
echo "Test 3: GET overview (filter: pending)"
echo "-----------------------------------"
curl -s "$BASE_URL/api/voucher-control/overview?client_id=$CLIENT_ID&filter=pending" | jq '.'
echo ""
echo ""

# Test 4: GET overview (filter: corrected)
echo "Test 4: GET overview (filter: corrected)"
echo "-----------------------------------"
curl -s "$BASE_URL/api/voucher-control/overview?client_id=$CLIENT_ID&filter=corrected" | jq '.'
echo ""
echo ""

# Test 5: GET overview (filter by voucher_type)
echo "Test 5: GET overview (filter: voucher_type=supplier_invoice)"
echo "-----------------------------------"
curl -s "$BASE_URL/api/voucher-control/overview?client_id=$CLIENT_ID&voucher_type=supplier_invoice" | jq '.'
echo ""
echo ""

# Test 6: GET overview with date range
echo "Test 6: GET overview (with date range)"
echo "-----------------------------------"
START_DATE="2026-02-01"
END_DATE="2026-02-28"
curl -s "$BASE_URL/api/voucher-control/overview?client_id=$CLIENT_ID&start_date=$START_DATE&end_date=$END_DATE" | jq '.'
echo ""
echo ""

# Test 7: GET audit trail for a specific voucher
echo "Test 7: GET audit trail for specific voucher"
echo "-----------------------------------"
# First, get a voucher ID from the overview
VOUCHER_ID=$(curl -s "$BASE_URL/api/voucher-control/overview?client_id=$CLIENT_ID&limit=1" | jq -r '.items[0].voucher_id // empty')

if [ -n "$VOUCHER_ID" ]; then
    echo "Testing with voucher ID: $VOUCHER_ID"
    curl -s "$BASE_URL/api/voucher-control/$VOUCHER_ID/audit-trail" | jq '.'
else
    echo "No vouchers found to test audit trail"
fi
echo ""
echo ""

# Test 8: GET voucher control stats
echo "Test 8: GET voucher control statistics"
echo "-----------------------------------"
curl -s "$BASE_URL/api/voucher-control/stats?client_id=$CLIENT_ID" | jq '.'
echo ""
echo ""

# Test 9: GET stats with date range
echo "Test 9: GET statistics (with date range)"
echo "-----------------------------------"
curl -s "$BASE_URL/api/voucher-control/stats?client_id=$CLIENT_ID&start_date=$START_DATE&end_date=$END_DATE" | jq '.'
echo ""
echo ""

echo "=========================================="
echo "All tests completed!"
echo "=========================================="
