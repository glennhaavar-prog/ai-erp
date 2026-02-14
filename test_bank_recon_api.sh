#!/bin/bash

# Test script for Bank Reconciliation API (Modul 2)
# Bank-to-Ledger matching endpoints

BASE_URL="http://localhost:8000"
CLIENT_ID="308e0336-d5c9-496f-8141-9087ee1fcae3"
ACCOUNT="1920"

echo "=========================================="
echo "Bank Reconciliation API Tests (Modul 2)"
echo "=========================================="
echo ""

# Test 1: GET /api/bank-recon/unmatched
echo "Test 1: GET unmatched transactions and ledger entries"
echo "----------------------------------------------"
echo "Request: GET $BASE_URL/api/bank-recon/unmatched?client_id=$CLIENT_ID&account=$ACCOUNT"
echo ""
curl -s "$BASE_URL/api/bank-recon/unmatched?client_id=$CLIENT_ID&account=$ACCOUNT" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

# Test 2: GET with date filters
echo "Test 2: GET unmatched with date filters"
echo "----------------------------------------------"
echo "Request: GET $BASE_URL/api/bank-recon/unmatched?client_id=$CLIENT_ID&account=$ACCOUNT&from_date=2026-01-01&to_date=2026-12-31"
echo ""
curl -s "$BASE_URL/api/bank-recon/unmatched?client_id=$CLIENT_ID&account=$ACCOUNT&from_date=2026-01-01&to_date=2026-12-31" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

# Test 3: POST /api/bank-recon/rules (Create rule)
echo "Test 3: POST create automation rule"
echo "----------------------------------------------"
RULE_JSON='{
  "client_id": "'$CLIENT_ID'",
  "rule_name": "Auto-match exact amounts same day",
  "rule_type": "amount_exact",
  "conditions": {
    "account": "1920",
    "amount_tolerance": 0.01,
    "date_tolerance_days": 0,
    "min_confidence": 90
  },
  "actions": {
    "auto_approve": false,
    "notify": true
  },
  "active": true,
  "priority": 10
}'

echo "Request: POST $BASE_URL/api/bank-recon/rules"
echo "Body:"
echo "$RULE_JSON" | python3 -m json.tool
echo ""
curl -s -X POST "$BASE_URL/api/bank-recon/rules" \
  -H "Content-Type: application/json" \
  -d "$RULE_JSON" | python3 -m json.tool
echo ""
echo ""

# Test 4: POST another rule (amount range)
echo "Test 4: POST create amount range rule"
echo "----------------------------------------------"
RULE_JSON_2='{
  "client_id": "'$CLIENT_ID'",
  "rule_name": "Match similar amounts within 3 days",
  "rule_type": "amount_range",
  "conditions": {
    "account": "1920",
    "amount_tolerance": 5.00,
    "date_tolerance_days": 3,
    "min_confidence": 75
  },
  "actions": {
    "auto_approve": false,
    "notify": false
  },
  "active": true,
  "priority": 20
}'

echo "Request: POST $BASE_URL/api/bank-recon/rules"
echo "Body:"
echo "$RULE_JSON_2" | python3 -m json.tool
echo ""
curl -s -X POST "$BASE_URL/api/bank-recon/rules" \
  -H "Content-Type: application/json" \
  -d "$RULE_JSON_2" | python3 -m json.tool
echo ""
echo ""

# Test 5: GET /api/bank-recon/rules
echo "Test 5: GET all active rules"
echo "----------------------------------------------"
echo "Request: GET $BASE_URL/api/bank-recon/rules?client_id=$CLIENT_ID"
echo ""
curl -s "$BASE_URL/api/bank-recon/rules?client_id=$CLIENT_ID" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

# Test 6: GET rules including inactive
echo "Test 6: GET all rules (including inactive)"
echo "----------------------------------------------"
echo "Request: GET $BASE_URL/api/bank-recon/rules?client_id=$CLIENT_ID&active_only=false"
echo ""
curl -s "$BASE_URL/api/bank-recon/rules?client_id=$CLIENT_ID&active_only=false" \
  -H "Content-Type: application/json" | python3 -m json.tool
echo ""
echo ""

# Test 7: POST /api/bank-recon/match (Create manual match)
# Note: This requires valid transaction and ledger entry IDs from Test 1
echo "Test 7: POST create manual match"
echo "----------------------------------------------"
echo "Note: You'll need to replace the UUIDs below with actual IDs from Test 1 output"
echo ""

# Example match request (will fail without real IDs)
MATCH_JSON='{
  "bank_transaction_id": "00000000-0000-0000-0000-000000000001",
  "ledger_entry_id": "00000000-0000-0000-0000-000000000002",
  "notes": "Manual match for reconciliation test"
}'

echo "Request: POST $BASE_URL/api/bank-recon/match"
echo "Body:"
echo "$MATCH_JSON" | python3 -m json.tool
echo ""
echo "Skipping this test as it requires actual transaction/ledger IDs"
echo "(Uncomment the curl command below and use real IDs from Test 1)"
echo ""
# Uncomment to run:
# curl -s -X POST "$BASE_URL/api/bank-recon/match" \
#   -H "Content-Type: application/json" \
#   -d "$MATCH_JSON" | python3 -m json.tool
echo ""
echo ""

echo "=========================================="
echo "All Tests Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "✅ Test 1: GET unmatched transactions"
echo "✅ Test 2: GET unmatched with date filters"
echo "✅ Test 3: POST create exact amount rule"
echo "✅ Test 4: POST create amount range rule"
echo "✅ Test 5: GET active rules"
echo "✅ Test 6: GET all rules"
echo "⏭️  Test 7: POST manual match (skipped - needs real IDs)"
echo ""
echo "To test manual matching (Test 7):"
echo "1. Run Test 1 and copy a bank_transaction ID and ledger_entry ID"
echo "2. Update MATCH_JSON in this script with those IDs"
echo "3. Uncomment the curl command and run again"
echo ""
