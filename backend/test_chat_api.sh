#!/bin/bash

# Test script for Chat API
# Demonstrates all chat functionality with curl

CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"
BASE_URL="http://localhost:8000/api/chat"

echo "========================================="
echo "Chat API Test Suite"
echo "========================================="
echo

# Test 1: Health check
echo "TEST 1: Health Check"
curl -s "${BASE_URL}/health" | python3 -m json.tool
echo
echo

# Test 2: Show review queue
echo "TEST 2: Show Review Queue"
curl -s -X POST "${BASE_URL}/" \
  -H "Content-Type: application/json" \
  -d "{\"client_id\": \"${CLIENT_ID}\", \"message\": \"show review queue\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['message']); print(f\"\nItems: {d['data']['count']}\")"
echo
echo

# Test 3: Workload status
echo "TEST 3: Workload Status"
curl -s -X POST "${BASE_URL}/" \
  -H "Content-Type: application/json" \
  -d "{\"client_id\": \"${CLIENT_ID}\", \"message\": \"workload\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['message'])"
echo
echo

# Test 4: Convenience endpoint - Get queue
echo "TEST 4: Convenience Endpoint - Get Queue"
curl -s "${BASE_URL}/queue/${CLIENT_ID}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Queue count: {d['data']['count']}\")"
echo
echo

echo "========================================="
echo "All tests completed!"
echo "========================================="
