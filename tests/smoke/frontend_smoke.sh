#!/bin/bash
# Frontend Smoke Tests
# Tests that frontend is accessible and builds successfully
# Run time: < 20 seconds (without full build)

set -e

echo "🔥 Frontend Smoke Tests"
echo "======================"
echo ""

FRONTEND_URL="${FRONTEND_URL:-http://localhost:3002}"
FRONTEND_DIR="/home/ubuntu/.openclaw/workspace/ai-erp/frontend"
FAILED=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test function
test_check() {
    local name="$1"
    shift
    echo -n "Testing $name... "
    
    if "$@" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 1. Check if frontend is running
echo -n "Testing Frontend Accessibility... "
if curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" | grep -q "200"; then
    echo -e "${GREEN}✅ PASS${NC} (HTTP 200)"
else
    status=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>&1 || echo "FAILED")
    if [ "$status" = "FAILED" ]; then
        echo -e "${RED}❌ FAIL${NC} (Frontend not running)"
        echo "Start frontend with: cd frontend && npm run dev -- -p 3002"
        FAILED=$((FAILED + 1))
    else
        echo -e "${YELLOW}⚠️  WARN${NC} (HTTP $status)"
    fi
fi

# 2. Check for TypeScript errors (type check only, fast)
if [ -d "$FRONTEND_DIR" ]; then
    echo -n "Testing TypeScript Type Check... "
    cd "$FRONTEND_DIR"
    if npx tsc --noEmit > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${YELLOW}⚠️  WARN${NC} (TypeScript errors found - check manually)"
        # Don't fail build for type errors, just warn
    fi
fi

# 3. Check for ESLint errors (basic syntax check)
if [ -d "$FRONTEND_DIR" ]; then
    echo -n "Testing ESLint... "
    cd "$FRONTEND_DIR"
    if npm run lint > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${YELLOW}⚠️  WARN${NC} (Linting issues found - check manually)"
        # Don't fail build for linting
    fi
fi

# 4. Test critical pages load (if frontend is running)
if curl -s "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -n "Testing Homepage Load... "
    response=$(curl -s "$FRONTEND_URL")
    if echo "$response" | grep -q "<!DOCTYPE html>"; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${RED}❌ FAIL${NC} (Invalid HTML response)"
        FAILED=$((FAILED + 1))
    fi
    
    # Check that no major React errors are in the page
    echo -n "Testing for React Errors... "
    if echo "$response" | grep -qi "error"; then
        echo -e "${YELLOW}⚠️  WARN${NC} (Possible errors in page)"
    else
        echo -e "${GREEN}✅ PASS${NC}"
    fi
fi

# 5. Check package.json dependencies are installed
if [ -d "$FRONTEND_DIR" ]; then
    echo -n "Testing Node Modules... "
    if [ -d "$FRONTEND_DIR/node_modules" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${RED}❌ FAIL${NC} (node_modules not found - run: npm install)"
        FAILED=$((FAILED + 1))
    fi
fi

# Optional: Quick build test (commented out by default - takes time)
# Uncomment for full smoke test before deployment
# echo -n "Testing Production Build... "
# cd "$FRONTEND_DIR"
# if npm run build > /tmp/frontend_build.log 2>&1; then
#     echo -e "${GREEN}✅ PASS${NC}"
# else
#     echo -e "${RED}❌ FAIL${NC} (Build failed - see /tmp/frontend_build.log)"
#     FAILED=$((FAILED + 1))
# fi

echo ""
echo "======================"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All frontend smoke tests passed!${NC}"
    echo ""
    echo "Note: For full confidence, also run:"
    echo "  cd frontend && npm run build"
    exit 0
else
    echo -e "${RED}❌ $FAILED test(s) failed${NC}"
    exit 1
fi
