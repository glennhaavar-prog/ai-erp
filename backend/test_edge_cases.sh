#!/bin/bash

echo "=== Edge Case Testing ==="
echo ""

# Test 1: Invalid client_id format
echo "Test 1: Invalid client_id format"
curl -s "http://localhost:8000/api/other-vouchers/pending?client_id=invalid-uuid" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if data.get('detail') and 'Invalid client_id' in data['detail'] else '✗ FAIL')"

# Test 2: Invalid voucher_id format
echo "Test 2: Invalid voucher_id format"
curl -s "http://localhost:8000/api/other-vouchers/not-a-uuid" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if data.get('detail') else '✗ FAIL')"

# Test 3: Non-existent voucher_id
echo "Test 3: Non-existent voucher_id"
curl -s "http://localhost:8000/api/other-vouchers/00000000-0000-0000-0000-000000000000" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if data.get('detail') and 'not found' in data['detail'] else '✗ FAIL')"

# Test 4: Invalid type filter
echo "Test 4: Invalid type filter"
curl -s "http://localhost:8000/api/other-vouchers/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&type=invalid_type" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if data.get('detail') and 'Invalid type' in data['detail'] else '✗ FAIL')"

# Test 5: Invalid priority filter
echo "Test 5: Invalid priority filter"
curl -s "http://localhost:8000/api/other-vouchers/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&priority=super_high" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if data.get('detail') and 'Invalid priority' in data['detail'] else '✗ FAIL')"

# Test 6: Empty results (non-existent client)
echo "Test 6: Empty results (non-existent client)"
curl -s "http://localhost:8000/api/other-vouchers/pending?client_id=00000000-0000-0000-0000-000000000001" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if data.get('items') == [] and data.get('total') == 0 else '✗ FAIL')"

# Test 7: Stats with non-existent client
echo "Test 7: Stats with non-existent client"
curl -s "http://localhost:8000/api/other-vouchers/stats?client_id=00000000-0000-0000-0000-000000000001" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if 'pending_by_type' in data else '✗ FAIL')"

# Test 8: Approve with invalid UUID
echo "Test 8: Approve with invalid UUID"
curl -s -X POST "http://localhost:8000/api/other-vouchers/invalid-uuid/approve" \
  -H "Content-Type: application/json" \
  -d '{"notes":"test"}' | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if data.get('detail') and 'Invalid UUID' in data['detail'] else '✗ FAIL')"

# Test 9: Reject without required field
echo "Test 9: Reject without required booking entries"
curl -s -X POST "http://localhost:8000/api/other-vouchers/a0900caf-d3e0-4c51-9a52-8326b4570b81/reject" \
  -H "Content-Type: application/json" \
  -d '{"notes":"test"}' | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if data.get('detail') and 'required' in data['detail'].lower() else '✗ FAIL')"

# Test 10: Pagination
echo "Test 10: Pagination with page_size=1"
curl -s "http://localhost:8000/api/other-vouchers/pending?client_id=09409ccf-d23e-45e5-93b9-68add0b96277&page_size=1" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ PASS' if len(data.get('items', [])) <= 1 else '✗ FAIL')"

echo ""
echo "=== Edge Case Testing Complete ==="
