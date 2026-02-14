#!/bin/bash

echo "=== FINAL ENDPOINT VERIFICATION ==="
echo ""

# Test new endpoint 1: GET single voucher
echo "1. Testing GET /api/other-vouchers/{voucher_id}"
RESPONSE=$(curl -s "http://localhost:8000/api/other-vouchers/a0900caf-d3e0-4c51-9a52-8326b4570b81")
if echo "$RESPONSE" | grep -q '"id"' && echo "$RESPONSE" | grep -q '"type"' && echo "$RESPONSE" | grep -q '"ai_confidence"'; then
    echo "   ✓ PASS - Endpoint returns full voucher details"
else
    echo "   ✗ FAIL - Endpoint response incomplete"
fi

# Test new endpoint 2: GET stats
echo "2. Testing GET /api/other-vouchers/stats"
RESPONSE=$(curl -s "http://localhost:8000/api/other-vouchers/stats?client_id=09409ccf-d23e-45e5-93b9-68add0b96277")
if echo "$RESPONSE" | grep -q '"pending_by_type"' && echo "$RESPONSE" | grep -q '"avg_confidence_by_type"' && echo "$RESPONSE" | grep -q '"approved"'; then
    echo "   ✓ PASS - Stats endpoint returns complete statistics"
else
    echo "   ✗ FAIL - Stats endpoint response incomplete"
fi

# Verify routing fix: /pending should not be caught by /{voucher_id}
echo "3. Verifying routing fix (/pending not caught by /{voucher_id})"
RESPONSE=$(curl -s "http://localhost:8000/api/other-vouchers/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277")
if echo "$RESPONSE" | grep -q '"items"' && echo "$RESPONSE" | grep -q '"total"'; then
    echo "   ✓ PASS - /pending route works correctly"
else
    echo "   ✗ FAIL - Routing issue detected"
fi

echo ""
echo "=== ALL ENDPOINTS VERIFIED ==="
