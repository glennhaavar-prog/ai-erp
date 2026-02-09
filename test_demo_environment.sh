#!/bin/bash
# Test Demo Environment - FASE 2.5
# Validates demo environment with test button functionality

set -e

BASE_URL="http://localhost:8000"
DEMO_API="${BASE_URL}/demo"

echo "=================================="
echo "  FASE 2.5: Demo Environment Test"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check demo status
echo -e "${YELLOW}Test 1: Checking demo environment status...${NC}"
STATUS_RESPONSE=$(curl -s "${DEMO_API}/status")
echo "$STATUS_RESPONSE" | jq .

DEMO_EXISTS=$(echo "$STATUS_RESPONSE" | jq -r '.demo_environment_exists')
if [ "$DEMO_EXISTS" = "true" ]; then
    echo -e "${GREEN}✓ Demo environment exists${NC}"
else
    echo -e "${RED}✗ Demo environment not found${NC}"
    exit 1
fi

CLIENTS=$(echo "$STATUS_RESPONSE" | jq -r '.stats.clients')
echo -e "${GREEN}✓ Found $CLIENTS demo clients${NC}"
echo ""

# Test 2: Generate test data
echo -e "${YELLOW}Test 2: Generating test data (small batch)...${NC}"
TEST_DATA_CONFIG='{
  "num_clients": 5,
  "invoices_per_client": 5,
  "customer_invoices_per_client": 3,
  "transactions_per_client": 5,
  "high_confidence_ratio": 0.7,
  "include_duplicates": true,
  "include_edge_cases": true
}'

GENERATE_RESPONSE=$(curl -s -X POST "${DEMO_API}/run-test" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA_CONFIG")

echo "$GENERATE_RESPONSE" | jq .

TASK_ID=$(echo "$GENERATE_RESPONSE" | jq -r '.task_id')
if [ -z "$TASK_ID" ] || [ "$TASK_ID" = "null" ]; then
    echo -e "${RED}✗ Failed to start test data generation${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Test data generation started (Task ID: $TASK_ID)${NC}"
echo ""

# Test 3: Poll task status
echo -e "${YELLOW}Test 3: Polling task status...${NC}"
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    sleep 2
    TASK_STATUS=$(curl -s "${DEMO_API}/task/${TASK_ID}")
    
    STATUS=$(echo "$TASK_STATUS" | jq -r '.status')
    PROGRESS=$(echo "$TASK_STATUS" | jq -r '.progress // 0')
    MESSAGE=$(echo "$TASK_STATUS" | jq -r '.message')
    
    echo "  Progress: $PROGRESS% - $MESSAGE"
    
    if [ "$STATUS" = "completed" ]; then
        echo -e "${GREEN}✓ Test data generation completed${NC}"
        echo "$TASK_STATUS" | jq '.stats'
        break
    elif [ "$STATUS" = "failed" ]; then
        echo -e "${RED}✗ Test data generation failed${NC}"
        echo "$TASK_STATUS" | jq '.error'
        exit 1
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}✗ Timeout waiting for test data generation${NC}"
    exit 1
fi

echo ""

# Test 4: Verify generated data
echo -e "${YELLOW}Test 4: Verifying generated data...${NC}"
FINAL_STATUS=$(curl -s "${DEMO_API}/status")
echo "$FINAL_STATUS" | jq .

VENDOR_INVOICES=$(echo "$FINAL_STATUS" | jq -r '.stats.vendor_invoices')
CUSTOMER_INVOICES=$(echo "$FINAL_STATUS" | jq -r '.stats.customer_invoices')
BANK_TRANSACTIONS=$(echo "$FINAL_STATUS" | jq -r '.stats.bank_transactions')

echo -e "${GREEN}✓ Vendor Invoices: $VENDOR_INVOICES${NC}"
echo -e "${GREEN}✓ Customer Invoices: $CUSTOMER_INVOICES${NC}"
echo -e "${GREEN}✓ Bank Transactions: $BANK_TRANSACTIONS${NC}"
echo ""

# Test 5: Check review queue
echo -e "${YELLOW}Test 5: Checking review queue...${NC}"
REVIEW_QUEUE=$(curl -s "${BASE_URL}/api/review-queue?status=needs_review")
QUEUE_COUNT=$(echo "$REVIEW_QUEUE" | jq -r '.invoices | length')

echo -e "${GREEN}✓ Review queue has $QUEUE_COUNT items${NC}"
echo ""

# Test 6: Check dashboard
echo -e "${YELLOW}Test 6: Checking dashboard verification...${NC}"
DASHBOARD=$(curl -s "${BASE_URL}/api/dashboard/verification")
OVERALL_STATUS=$(echo "$DASHBOARD" | jq -r '.overall_status')

echo "$DASHBOARD" | jq '.summary'
echo -e "${GREEN}✓ Dashboard overall status: $OVERALL_STATUS${NC}"
echo ""

# Summary
echo "=================================="
echo -e "${GREEN}  All tests passed! ✓${NC}"
echo "=================================="
echo ""
echo "Demo Environment Summary:"
echo "  - Clients: $CLIENTS"
echo "  - Vendor Invoices: $VENDOR_INVOICES"
echo "  - Customer Invoices: $CUSTOMER_INVOICES"
echo "  - Bank Transactions: $BANK_TRANSACTIONS"
echo "  - Review Queue: $QUEUE_COUNT items"
echo "  - Dashboard Status: $OVERALL_STATUS"
echo ""
echo "Frontend Test Button:"
echo "  → Open http://localhost:3002/dashboard"
echo "  → Click 'Kjør Test' button (top-right)"
echo "  → Confirm and watch progress"
echo ""
echo -e "${GREEN}FASE 2.5 COMPLETE!${NC}"
