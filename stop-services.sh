#!/bin/bash
# STOP-SERVICES.sh - Stop all Kontali services

echo "=========================================="
echo "  KONTALI - Stopping Services"
echo "=========================================="
echo ""

# Kill backend
if [ -f /tmp/kontali-backend.pid ]; then
    PID=$(cat /tmp/kontali-backend.pid)
    echo -n "Stopping backend (PID $PID)... "
    kill $PID 2>/dev/null && echo "✓ Stopped" || echo "Already stopped"
    rm -f /tmp/kontali-backend.pid
else
    echo "Backend: No PID file found"
    pkill -f "uvicorn.*app.main:app" && echo "✓ Killed backend process"
fi

# Kill frontend
if [ -f /tmp/kontali-frontend.pid ]; then
    PID=$(cat /tmp/kontali-frontend.pid)
    echo -n "Stopping frontend (PID $PID)... "
    kill $PID 2>/dev/null && echo "✓ Stopped" || echo "Already stopped"
    rm -f /tmp/kontali-frontend.pid
else
    echo "Frontend: No PID file found"
    pkill -f "next-server" && echo "✓ Killed frontend process"
fi

echo ""
echo "Services stopped."
