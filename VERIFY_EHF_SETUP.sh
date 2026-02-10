#!/bin/bash
#
# EHF Test Environment Verification Script
# Verifies all files are present and properly configured
#

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     EHF Test Environment - Setup Verification             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1 (MISSING)"
        ((FAILED++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1/ (MISSING)"
        ((FAILED++))
    fi
}

echo "📁 Checking files and directories..."
echo ""

echo "Backend API:"
check_file "backend/app/api/routes/test_ehf.py"
echo ""

echo "Sample EHF Files:"
check_dir "backend/tests/fixtures/ehf"
check_file "backend/tests/fixtures/ehf/ehf_sample_1_simple.xml"
check_file "backend/tests/fixtures/ehf/ehf_sample_2_multi_line.xml"
check_file "backend/tests/fixtures/ehf/ehf_sample_3_zero_vat.xml"
check_file "backend/tests/fixtures/ehf/ehf_sample_4_reverse_charge.xml"
check_file "backend/tests/fixtures/ehf/ehf_sample_5_credit_note.xml"
echo ""

echo "CLI Test Script:"
check_file "backend/scripts/test_ehf.sh"
if [ -f "backend/scripts/test_ehf.sh" ]; then
    if [ -x "backend/scripts/test_ehf.sh" ]; then
        echo -e "${GREEN}  ✓ Executable${NC}"
    else
        echo -e "${YELLOW}  ⚠ Not executable (run: chmod +x backend/scripts/test_ehf.sh)${NC}"
    fi
fi
echo ""

echo "E2E Tests:"
check_file "backend/tests/test_ehf_e2e.py"
echo ""

echo "Documentation:"
check_file "backend/EHF_TESTING_GUIDE.md"
check_file "EHF_TEST_ENVIRONMENT_COMPLETE.md"
echo ""

echo "Frontend UI:"
check_file "frontend/src/app/test/ehf/page.tsx"
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All files present!${NC}"
    echo ""
    echo "🚀 Quick Start:"
    echo ""
    echo "  1. Start backend:"
    echo -e "     ${YELLOW}cd ai-erp && docker-compose up backend -d${NC}"
    echo ""
    echo "  2. Test via CLI:"
    echo -e "     ${YELLOW}./backend/scripts/test_ehf.sh backend/tests/fixtures/ehf/ehf_sample_1_simple.xml${NC}"
    echo ""
    echo "  3. Test via Web UI:"
    echo -e "     ${YELLOW}http://localhost:3000/test/ehf${NC}"
    echo ""
    echo "  4. Run E2E tests:"
    echo -e "     ${YELLOW}cd backend && pytest tests/test_ehf_e2e.py -v${NC}"
    echo ""
    echo "📖 Full documentation:"
    echo "   backend/EHF_TESTING_GUIDE.md"
    echo ""
else
    echo -e "${RED}❌ Some files are missing!${NC}"
    echo ""
    echo "Please ensure all files are properly created."
    exit 1
fi
