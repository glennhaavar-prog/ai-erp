#!/bin/bash
# VERIFY-FULL-STACK.sh - Grundig test av HELE stacken

echo "=========================================="
echo "  KONTALI - Full Stack Verification"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_pattern="$3"
    
    echo -n "Testing $name... "
    
    response=$(curl -s "$url" 2>&1)
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1)
    
    if [ "$http_code" != "200" ]; then
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
        FAIL=$((FAIL + 1))
        return 1
    fi
    
    if echo "$response" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✓ PASS${NC}"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Pattern not found: $expected_pattern)"
        echo "  Response preview: ${response:0:100}..."
        FAIL=$((FAIL + 1))
        return 1
    fi
}

echo "=== Backend Tests ==="
test_endpoint "Health check" "http://localhost:8000/health" '"status":"healthy"'
test_endpoint "API docs" "http://localhost:8000/docs" "swagger"
test_endpoint "OpenAPI spec" "http://localhost:8000/openapi.json" '"openapi"'
echo ""

echo "=== Frontend Tests ==="
test_endpoint "Root page" "http://localhost:3002" "Kontali"
test_endpoint "Multi-client page" "http://localhost:3002/multi-client" "Multi-klient Oversikt"
echo ""

echo "=== Port Binding Tests ==="
echo -n "Backend bound to 0.0.0.0:8000... "
if ss -tlnp 2>/dev/null | grep ":8000 " | grep -q "0.0.0.0"; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    FAIL=$((FAIL + 1))
fi

echo -n "Frontend bound to *:3002... "
if ss -tlnp 2>/dev/null | grep ":3002 " | grep -q "\*:3002"; then
    echo -e "${GREEN}✓ PASS${NC}"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "=========================================="
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC} ($PASS/$((PASS + FAIL)))"
    echo "=========================================="
    echo ""
    echo "Glenn kan nå koble til med SSH-tunnel!"
    echo "Instruksjon: Dobbeltklikk 'start-tunnels-only.bat'"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC} ($PASS passed, $FAIL failed)"
    echo "=========================================="
    echo ""
    echo "Troubleshooting:"
    echo "  - Check logs: tail -50 /tmp/kontali-backend.log"
    echo "  - Check logs: tail -50 /tmp/kontali-frontend.log"
    echo "  - Restart: ./stop-services.sh && ./start-services.sh"
    exit 1
fi
