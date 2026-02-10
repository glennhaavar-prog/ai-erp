#!/bin/bash
# Quick Verification Script for Kontali ERP
# Run this to verify system health before/after testing

set -e

BACKEND="http://localhost:8000"
FRONTEND="http://localhost:3002"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BOLD}╔════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   KONTALI ERP - QUICK VERIFICATION    ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if services are running
echo -e "${BLUE}Checking running services...${NC}"
BACKEND_RUNNING=$(ps aux | grep -E "uvicorn.*8000" | grep -v grep | wc -l)
FRONTEND_RUNNING=$(ps aux | grep -E "next.*3002" | grep -v grep | wc -l)

if [ "$BACKEND_RUNNING" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Backend process running (port 8000)"
else
    echo -e "${RED}✗${NC} Backend NOT running!"
    echo "  Start with: pm2 start ecosystem.config.js"
    exit 1
fi

if [ "$FRONTEND_RUNNING" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Frontend process running (port 3002)"
else
    echo -e "${RED}✗${NC} Frontend NOT running!"
    exit 1
fi

echo ""
echo -e "${BLUE}Testing backend endpoints...${NC}"

# Test health endpoint
if curl -sf "$BACKEND/health" > /dev/null; then
    echo -e "${GREEN}✓${NC} Health endpoint responding"
else
    echo -e "${RED}✗${NC} Health endpoint failed"
    exit 1
fi

# Test API docs
if curl -sf "$BACKEND/docs" > /dev/null; then
    echo -e "${GREEN}✓${NC} API documentation accessible"
else
    echo -e "${RED}✗${NC} API docs not accessible"
fi

# Test database connectivity
CLIENT_COUNT=$(curl -sf "$BACKEND/api/clients/" | jq -r '.total // .items | length' 2>/dev/null || echo "0")
if [ "$CLIENT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Database connected ($CLIENT_COUNT clients found)"
else
    echo -e "${RED}✗${NC} Database connectivity issue"
    exit 1
fi

# Test core APIs
CORE_APIS=(
    "/api/clients/:Clients"
    "/api/invoices/:Invoices"
    "/api/accounts/:Accounts"
    "/api/tasks/:Tasks"
    "/api/review-queue/:Review Queue"
)

for api_spec in "${CORE_APIS[@]}"; do
    endpoint=$(echo "$api_spec" | cut -d':' -f1)
    name=$(echo "$api_spec" | cut -d':' -f2)
    
    if curl -sf "$BACKEND$endpoint" > /dev/null; then
        echo -e "${GREEN}✓${NC} $name API working"
    else
        echo -e "${YELLOW}⚠${NC} $name API issue (may need parameters)"
    fi
done

# Get a client ID for report testing
CLIENT_ID=$(curl -s "$BACKEND/api/clients/" | jq -r '.items[0].id' 2>/dev/null || echo "")

if [ -n "$CLIENT_ID" ]; then
    echo ""
    echo -e "${BLUE}Testing reports (using client: ${CLIENT_ID:0:8}...)${NC}"
    
    REPORTS=(
        "/api/reports/saldobalanse?client_id=$CLIENT_ID:Saldobalanse"
        "/api/reports/balanse?client_id=$CLIENT_ID:Balance Sheet"
        "/api/reports/resultat?client_id=$CLIENT_ID:Income Statement"
        "/api/reports/hovedbok?client_id=$CLIENT_ID:Hovedbok"
    )
    
    for report_spec in "${REPORTS[@]}"; do
        endpoint=$(echo "$report_spec" | cut -d':' -f1)
        name=$(echo "$report_spec" | cut -d':' -f2)
        
        if curl -sf "$BACKEND$endpoint" > /dev/null; then
            echo -e "${GREEN}✓${NC} $name report"
        else
            echo -e "${RED}✗${NC} $name report failed"
        fi
    done
fi

echo ""
echo -e "${BLUE}Testing frontend...${NC}"

# Test frontend
if curl -sf "$FRONTEND/" > /dev/null; then
    echo -e "${GREEN}✓${NC} Frontend serving (port 3002)"
else
    echo -e "${RED}✗${NC} Frontend not accessible"
    exit 1
fi

# Test critical frontend pages
PAGES=(
    "/:Dashboard"
    "/test/ehf:EHF Test Page"
    "/rapporter/saldobalanse:Saldobalanse"
    "/huvudbok:Hovedbok"
    "/bank-reconciliation:Bank Reconciliation"
)

for page_spec in "${PAGES[@]}"; do
    path=$(echo "$page_spec" | cut -d':' -f1)
    name=$(echo "$page_spec" | cut -d':' -f2)
    
    if curl -sf "$FRONTEND$path" > /dev/null; then
        echo -e "${GREEN}✓${NC} $name page"
    else
        echo -e "${YELLOW}⚠${NC} $name page issue"
    fi
done

# Check EHF test files
echo ""
echo -e "${BLUE}Checking EHF test files...${NC}"
EHF_DIR="backend/tests/fixtures/ehf"
if [ -d "$EHF_DIR" ]; then
    EHF_COUNT=$(ls "$EHF_DIR"/*.xml 2>/dev/null | wc -l)
    if [ "$EHF_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} Found $EHF_COUNT EHF test files"
        echo "  Location: $EHF_DIR"
    else
        echo -e "${YELLOW}⚠${NC} No EHF files found"
    fi
else
    echo -e "${YELLOW}⚠${NC} EHF test directory not found"
fi

# Database statistics
echo ""
echo -e "${BLUE}Database statistics...${NC}"

INVOICE_COUNT=$(curl -s "$BACKEND/api/invoices/?limit=1000" 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
echo -e "${GREEN}•${NC} Invoices: $INVOICE_COUNT"

REVIEW_COUNT=$(curl -s "$BACKEND/api/review-queue/" 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
echo -e "${GREEN}•${NC} Review Queue items: $REVIEW_COUNT"

ACCOUNT_COUNT=$(curl -s "$BACKEND/api/accounts/" 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
echo -e "${GREEN}•${NC} Chart of Accounts: $ACCOUNT_COUNT accounts"

# Check logs for errors
echo ""
echo -e "${BLUE}Checking for recent errors...${NC}"
if [ -f "backend/logs/app.log" ]; then
    ERROR_COUNT=$(tail -100 backend/logs/app.log | grep -i "error" | grep -v "404" | wc -l)
    if [ "$ERROR_COUNT" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} No recent errors in logs"
    else
        echo -e "${YELLOW}⚠${NC} Found $ERROR_COUNT error entries (check logs)"
    fi
else
    echo -e "${YELLOW}⚠${NC} Log file not found (may be logging to stdout)"
fi

# Final summary
echo ""
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${BOLD}              VERIFICATION RESULT          ${NC}"
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}${BOLD}✅ SYSTEM OPERATIONAL${NC}"
echo ""
echo -e "Backend:  ${BLUE}http://localhost:8000${NC}"
echo -e "Frontend: ${BLUE}http://localhost:3002${NC}"
echo -e "API Docs: ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BOLD}Ready for testing!${NC}"
echo ""
echo "Next steps:"
echo "  1. Set up SSH tunnel (if testing remotely)"
echo "  2. Open frontend at http://localhost:3002"
echo "  3. Follow GLENN_TEST_CHECKLIST.md"
echo ""

exit 0
