#!/bin/bash
# START-SERVICES.sh - Start all Kontali services on EC2

set -e

echo "=========================================="
echo "  KONTALI - Starting Services on EC2"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$(dirname "$0")"

# Function to check if port is in use
check_port() {
    local port=$1
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        return 0  # Port in use
    else
        return 1  # Port free
    fi
}

# Function to start backend
start_backend() {
    echo -n "Backend (port 8000): "
    
    if check_port 8000; then
        echo -e "${YELLOW}Already running${NC}"
        return 0
    fi
    
    echo "Starting..."
    cd backend
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/kontali-backend.log 2>&1 &
    echo $! > /tmp/kontali-backend.pid
    cd ..
    
    sleep 3
    
    if check_port 8000; then
        echo -e "${GREEN}✓ Started${NC} (PID: $(cat /tmp/kontali-backend.pid))"
    else
        echo -e "${RED}✗ Failed to start${NC}"
        echo "Check log: tail -50 /tmp/kontali-backend.log"
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    echo -n "Frontend (port 3002): "
    
    if check_port 3002; then
        echo -e "${YELLOW}Already running${NC}"
        return 0
    fi
    
    echo "Starting..."
    cd frontend
    nohup npm run dev > /tmp/kontali-frontend.log 2>&1 &
    echo $! > /tmp/kontali-frontend.pid
    cd ..
    
    sleep 5
    
    if check_port 3002; then
        echo -e "${GREEN}✓ Started${NC} (PID: $(cat /tmp/kontali-frontend.pid))"
    else
        echo -e "${RED}✗ Failed to start${NC}"
        echo "Check log: tail -50 /tmp/kontali-frontend.log"
        return 1
    fi
}

# Start services
echo "=== Starting Services ==="
start_backend
start_frontend

echo ""
echo "=== Service Status ==="
ss -tlnp 2>/dev/null | grep -E ":(3002|8000)" || echo "No services found"

echo ""
echo "=========================================="
echo -e "${GREEN}Services started successfully!${NC}"
echo "=========================================="
echo ""
echo "Test connectivity:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:3002"
echo ""
echo "View logs:"
echo "  tail -f /tmp/kontali-backend.log"
echo "  tail -f /tmp/kontali-frontend.log"
