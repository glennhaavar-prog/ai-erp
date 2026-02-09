#!/bin/bash
# TEST-CONNECTIVITY.sh - Grundig test av hele stack

echo "=========================================="
echo "  KONTALI CONNECTIVITY TEST"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_service() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null)
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected, got $response)"
        return 1
    fi
}

# Test backend
echo "=== BACKEND (port 8000) ==="
test_service "Backend Health" "http://localhost:8000/health" "200"
test_service "Backend Docs" "http://localhost:8000/docs" "200"
test_service "Backend API" "http://localhost:8000/api/tenants" "200"
echo ""

# Test frontend
echo "=== FRONTEND (port 3002) ==="
test_service "Frontend Root" "http://localhost:3002" "200"
test_service "Frontend Multi-Client" "http://localhost:3002/multi-client" "200"
echo ""

# Check if services are actually running
echo "=== RUNNING PROCESSES ==="
echo -n "Backend (uvicorn): "
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo -e "${GREEN}✓ Running${NC} (PID: $(pgrep -f 'uvicorn.*app.main:app'))"
else
    echo -e "${RED}✗ Not running${NC}"
fi

echo -n "Frontend (next-server): "
if pgrep -f "next-server.*3002" > /dev/null; then
    echo -e "${GREEN}✓ Running${NC} (PID: $(pgrep -f 'next-server'))"
else
    echo -e "${RED}✗ Not running${NC}"
fi
echo ""

# Check ports
echo "=== PORT BINDINGS ==="
echo "Listening ports:"
ss -tlnp 2>/dev/null | grep -E ":(3002|8000|18789)" | while read line; do
    echo "  $line"
done
echo ""

# Test from external perspective (what Glenn sees)
echo "=== EXTERNAL ACCESS TEST ==="
echo "Testing if ports are reachable from outside..."
echo -n "Port 3002 (Frontend): "
if ss -tlnp 2>/dev/null | grep ":3002" | grep -q "0.0.0.0\|*:3002"; then
    echo -e "${GREEN}✓ Bound to 0.0.0.0 (accessible)${NC}"
else
    echo -e "${YELLOW}⚠ Only localhost (needs SSH tunnel)${NC}"
fi

echo -n "Port 8000 (Backend): "
if ss -tlnp 2>/dev/null | grep ":8000" | grep -q "0.0.0.0"; then
    echo -e "${GREEN}✓ Bound to 0.0.0.0 (accessible)${NC}"
else
    echo -e "${YELLOW}⚠ Only localhost (needs SSH tunnel)${NC}"
fi

echo ""
echo "=========================================="
echo "  Test completed"
echo "=========================================="
