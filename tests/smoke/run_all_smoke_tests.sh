#!/bin/bash
# Run All Smoke Tests
# Combines backend and frontend smoke tests
# Run before any deployment or major commit

echo "🔥🔥 Running All Smoke Tests 🔥🔥"
echo "=================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FAILED=0

# Run backend smoke tests
echo "▶️  Running Backend Smoke Tests..."
if "$SCRIPT_DIR/backend_smoke.sh"; then
    echo ""
else
    FAILED=$((FAILED + 1))
    echo ""
fi

# Run frontend smoke tests
echo "▶️  Running Frontend Smoke Tests..."
if "$SCRIPT_DIR/frontend_smoke.sh"; then
    echo ""
else
    FAILED=$((FAILED + 1))
    echo ""
fi

# Summary
echo "=================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ ALL SMOKE TESTS PASSED"
    echo ""
    echo "System is healthy and ready for deployment! 🚀"
    exit 0
else
    echo "❌ SOME SMOKE TESTS FAILED"
    echo ""
    echo "Fix the issues above before deploying."
    exit 1
fi
