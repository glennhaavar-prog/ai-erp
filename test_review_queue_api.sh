#!/bin/bash
# Test Review Queue API Endpoints
# Use client_id: 09409ccf-d23e-45e5-93b9-68add0b96277

BASE_URL="http://localhost:8000"
CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"

echo "=============================="
echo "Review Queue API Test"
echo "=============================="
echo ""

# Test 1: Get stats
echo "1. Testing GET /api/review-queue/stats..."
curl -s "${BASE_URL}/api/review-queue/stats?client_id=${CLIENT_ID}" | jq .
echo ""

# Test 2: Get queue items
echo "2. Testing GET /api/review-queue/?status=pending..."
RESPONSE=$(curl -s "${BASE_URL}/api/review-queue/?status=pending&client_id=${CLIENT_ID}")
echo "$RESPONSE" | jq '.items | length' 2>/dev/null || echo "Error parsing response: $RESPONSE"
echo ""

# Get first item ID if available
ITEM_ID=$(echo "$RESPONSE" | jq -r '.items[0].id' 2>/dev/null)

if [ "$ITEM_ID" != "null" ] && [ -n "$ITEM_ID" ]; then
    echo "3. Testing GET /api/review-queue/${ITEM_ID}..."
    curl -s "${BASE_URL}/api/review-queue/${ITEM_ID}" | jq '{id, supplier, amount, ai_confidence, status}'
    echo ""
    
    echo "Note: Approve and Correct endpoints are ready for testing:"
    echo "  POST /api/review-queue/{id}/approve"
    echo "  POST /api/review-queue/{id}/correct"
else
    echo "3. No pending items found to test detail endpoint"
fi

# Test 3: Get thresholds
echo ""
echo "4. Testing GET /api/clients/{id}/thresholds..."
curl -s "${BASE_URL}/api/clients/${CLIENT_ID}/thresholds" | jq .
echo ""

echo "=============================="
echo "API Tests Complete"
echo "=============================="
