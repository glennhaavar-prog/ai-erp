#!/bin/bash

echo "=== Null Handling Tests ==="
echo ""

# Test with a voucher to check all null fields are handled properly
CLIENT_ID="09409ccf-d23e-45e5-93b9-68add0b96277"

echo "Test 1: Check single voucher handles null fields"
curl -s "http://localhost:8000/api/other-vouchers/a0900caf-d3e0-4c51-9a52-8326b4570b81" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Check that all expected fields exist and nulls are handled gracefully
checks = [
    'id' in data,
    'assigned_to_user_id' in data,  # Can be null
    'resolved_at' in data,  # Can be null
    'ai_confidence' in data,  # Should have a default
    'ai_reasoning' in data,  # Should have default text
]
print('✓ PASS - All fields present and nulls handled' if all(checks) else '✗ FAIL')
"

echo "Test 2: Check pending list handles empty ai_confidence"
curl -s "http://localhost:8000/api/other-vouchers/pending?client_id=$CLIENT_ID&page_size=10" | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('items', [])
if not items:
    print('⊘ SKIP - No items to test')
else:
    # Check all items have ai_confidence (even if 0)
    all_have_confidence = all('ai_confidence' in item for item in items)
    all_have_reasoning = all('ai_reasoning' in item for item in items)
    print('✓ PASS - All items handle confidence/reasoning' if (all_have_confidence and all_have_reasoning) else '✗ FAIL')
"

echo "Test 3: Stats endpoint handles zero counts gracefully"
curl -s "http://localhost:8000/api/other-vouchers/stats?client_id=00000000-0000-0000-0000-000000000001" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Check structure is correct even with no data
checks = [
    'pending_by_type' in data,
    'avg_confidence_by_type' in data,
    'approved' in data,
    all(k in data['approved'] for k in ['today', 'this_week', 'this_month'])
]
print('✓ PASS - Stats handle empty data' if all(checks) else '✗ FAIL')
"

echo ""
echo "=== Null Handling Tests Complete ==="
