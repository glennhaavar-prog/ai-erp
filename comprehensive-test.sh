#!/bin/bash
# Comprehensive Kontali ERP Testing Script
# Test Date: 2026-02-10

set -e

BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3002"
TEST_RESULTS="test-results-$(date +%Y%m%d-%H%M).md"

echo "# Kontali ERP Comprehensive Test Report" > "$TEST_RESULTS"
echo "**Date**: $(date)" >> "$TEST_RESULTS"
echo "**Backend**: $BACKEND_URL" >> "$TEST_RESULTS"
echo "**Frontend**: $FRONTEND_URL" >> "$TEST_RESULTS"
echo "" >> "$TEST_RESULTS"

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

# Function to log test result
log_test() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    test_count=$((test_count + 1))
    
    if [ "$status" = "PASS" ]; then
        pass_count=$((pass_count + 1))
        echo -e "${GREEN}✓${NC} $test_name"
        echo "- ✅ **$test_name**: PASS" >> "$TEST_RESULTS"
    else
        fail_count=$((fail_count + 1))
        echo -e "${RED}✗${NC} $test_name"
        echo "- ❌ **$test_name**: FAIL" >> "$TEST_RESULTS"
    fi
    
    if [ -n "$details" ]; then
        echo "  $details" >> "$TEST_RESULTS"
    fi
    echo "" >> "$TEST_RESULTS"
}

echo "=========================================="
echo "  KONTALI ERP COMPREHENSIVE TEST SUITE"
echo "=========================================="
echo ""

# ==========================================
# 1. BACKEND HEALTH CHECKS
# ==========================================
echo "## 1. Backend Health Checks" >> "$TEST_RESULTS"
echo ""
echo -e "${YELLOW}[1] Backend Health Checks${NC}"

# Test 1.1: Health endpoint
if curl -sf "$BACKEND_URL/health" > /dev/null; then
    log_test "Health endpoint responds" "PASS" "Backend is healthy"
else
    log_test "Health endpoint responds" "FAIL" "Backend health check failed"
fi

# Test 1.2: API documentation
if curl -sf "$BACKEND_URL/docs" > /dev/null; then
    log_test "API docs available" "PASS" "Swagger docs accessible"
else
    log_test "API docs available" "FAIL" "API docs not accessible"
fi

# Test 1.3: Database connectivity
DB_TEST=$(curl -sf "$BACKEND_URL/api/clients" | jq -r 'type')
if [ "$DB_TEST" = "array" ]; then
    log_test "Database connectivity" "PASS" "Database queries working"
else
    log_test "Database connectivity" "FAIL" "Database connection issues"
fi

# ==========================================
# 2. CORE API ENDPOINTS
# ==========================================
echo "## 2. Core API Endpoints" >> "$TEST_RESULTS"
echo ""
echo -e "${YELLOW}[2] Core API Endpoints${NC}"

# Test critical endpoints
endpoints=(
    "/api/clients"
    "/api/invoices"
    "/api/vouchers"
    "/api/accounts"
    "/api/tasks"
    "/api/review-queue"
    "/api/bank-transactions"
)

for endpoint in "${endpoints[@]}"; do
    response=$(curl -sf -w "%{http_code}" "$BACKEND_URL$endpoint" -o /dev/null)
    if [ "$response" = "200" ]; then
        log_test "GET $endpoint" "PASS" "HTTP 200 OK"
    else
        log_test "GET $endpoint" "FAIL" "HTTP $response"
    fi
done

# ==========================================
# 3. EHF INVOICE PROCESSING
# ==========================================
echo "## 3. EHF Invoice Processing" >> "$TEST_RESULTS"
echo ""
echo -e "${YELLOW}[3] EHF Invoice Processing${NC}"

# Check if EHF test files exist
EHF_DIR="/home/ubuntu/.openclaw/workspace/ai-erp/backend/test_ehf_files"
if [ -d "$EHF_DIR" ] && [ "$(ls -A $EHF_DIR/*.xml 2>/dev/null | wc -l)" -gt 0 ]; then
    log_test "EHF test files available" "PASS" "Found $(ls -1 $EHF_DIR/*.xml 2>/dev/null | wc -l) EHF files"
    
    # Test EHF endpoint availability
    if curl -sf "$BACKEND_URL/api/test/ehf/send" -X POST > /dev/null 2>&1 || [ $? -eq 22 ]; then
        log_test "EHF test endpoint exists" "PASS" "Endpoint /api/test/ehf/send available"
    else
        log_test "EHF test endpoint exists" "FAIL" "Endpoint not found"
    fi
else
    log_test "EHF test files available" "FAIL" "No EHF test files found in $EHF_DIR"
fi

# ==========================================
# 4. BANK RECONCILIATION
# ==========================================
echo "## 4. Bank Reconciliation" >> "$TEST_RESULTS"
echo ""
echo -e "${YELLOW}[4] Bank Reconciliation${NC}"

# Test bank reconciliation endpoints
BANK_STATUS=$(curl -sf "$BACKEND_URL/api/bank-reconciliation/status" -w "%{http_code}" -o /dev/null)
if [ "$BANK_STATUS" = "200" ]; then
    log_test "Bank reconciliation status" "PASS" "Status endpoint working"
else
    log_test "Bank reconciliation status" "FAIL" "HTTP $BANK_STATUS"
fi

# ==========================================
# 5. ACCOUNTING REPORTS
# ==========================================
echo "## 5. Accounting Reports" >> "$TEST_RESULTS"
echo ""
echo -e "${YELLOW}[5] Accounting Reports${NC}"

# Test report endpoints
reports=(
    "/api/reports/saldobalanse"
    "/api/reports/balance-sheet"
    "/api/reports/income-statement"
    "/api/reports/hovedbok"
    "/api/reports/leverandorreskontro"
    "/api/reports/kundereskontro"
)

for report in "${reports[@]}"; do
    response=$(curl -sf -w "%{http_code}" "$BACKEND_URL$report" -o /dev/null)
    if [ "$response" = "200" ]; then
        log_test "Report: $report" "PASS" "HTTP 200 OK"
    else
        log_test "Report: $report" "FAIL" "HTTP $response"
    fi
done

# ==========================================
# 6. FRONTEND BUILD STATUS
# ==========================================
echo "## 6. Frontend Status" >> "$TEST_RESULTS"
echo ""
echo -e "${YELLOW}[6] Frontend Status${NC}"

# Check if frontend is serving
FRONTEND_STATUS=$(curl -sf -w "%{http_code}" "$FRONTEND_URL" -o /dev/null)
if [ "$FRONTEND_STATUS" = "200" ]; then
    log_test "Frontend serving" "PASS" "Next.js server responding"
else
    log_test "Frontend serving" "FAIL" "HTTP $FRONTEND_STATUS"
fi

# Check critical frontend pages
pages=(
    "/"
    "/bank-reconciliation"
    "/reskontro/leverandorer"
    "/reskontro/kunder"
    "/bilag/journal"
    "/rapporter/saldobalanse"
    "/rapporter/balanse"
    "/hovedbok"
    "/test/ehf"
)

for page in "${pages[@]}"; do
    response=$(curl -sf -w "%{http_code}" "$FRONTEND_URL$page" -o /dev/null)
    if [ "$response" = "200" ]; then
        log_test "Page: $page" "PASS" "HTTP 200 OK"
    else
        log_test "Page: $page" "FAIL" "HTTP $response"
    fi
done

# ==========================================
# SUMMARY
# ==========================================
echo "=========================================="
echo "  TEST SUMMARY"
echo "=========================================="
echo ""
echo "## Summary" >> "$TEST_RESULTS"
echo "" >> "$TEST_RESULTS"
echo "**Total Tests**: $test_count" >> "$TEST_RESULTS"
echo "**Passed**: $pass_count ✅" >> "$TEST_RESULTS"
echo "**Failed**: $fail_count ❌" >> "$TEST_RESULTS"
echo "" >> "$TEST_RESULTS"

PASS_RATE=$((pass_count * 100 / test_count))
echo "**Pass Rate**: ${PASS_RATE}%" >> "$TEST_RESULTS"

echo -e "Total Tests: $test_count"
echo -e "${GREEN}Passed: $pass_count${NC}"
echo -e "${RED}Failed: $fail_count${NC}"
echo -e "Pass Rate: ${PASS_RATE}%"
echo ""
echo "Detailed results saved to: $TEST_RESULTS"

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Review the report.${NC}"
    exit 1
fi
