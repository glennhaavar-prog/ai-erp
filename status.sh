#!/bin/bash
# STATUS.sh - Check Kontali service status

echo "=========================================="
echo "  KONTALI - Service Status"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check backend
echo -n "Backend (port 8000): "
if ss -tlnp 2>/dev/null | grep -q ":8000 "; then
    PID=$(ss -tlnp 2>/dev/null | grep ":8000 " | grep -oP 'pid=\K[0-9]+' | head -1)
    echo -e "${GREEN}✓ Running${NC} (PID: $PID)"
    curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "  (Health check unavailable)"
else
    echo -e "${RED}✗ Not running${NC}"
fi

# Check frontend  
echo -n "Frontend (port 3002): "
if ss -tlnp 2>/dev/null | grep -q ":3002 "; then
    PID=$(ss -tlnp 2>/dev/null | grep ":3002 " | grep -oP 'pid=\K[0-9]+' | head -1)
    echo -e "${GREEN}✓ Running${NC} (PID: $PID)"
else
    echo -e "${RED}✗ Not running${NC}"
fi

echo ""
echo "=== Port Bindings ==="
ss -tlnp 2>/dev/null | grep -E ":(3002|8000|18789)" || echo "No Kontali ports bound"

echo ""
echo "=== Recent Logs ==="
echo "Backend (last 5 lines):"
tail -5 /tmp/kontali-backend.log 2>/dev/null || echo "  No log file"

echo ""
echo "Frontend (last 5 lines):"
tail -5 /tmp/kontali-frontend.log 2>/dev/null || echo "  No log file"
