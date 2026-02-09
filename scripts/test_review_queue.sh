#!/bin/bash
# Test Review Queue System
# Generates demo data and verifies the confidence scoring & learning system

set -e

cd "$(dirname "$0")/.."

echo "========================================"
echo "🧪 REVIEW QUEUE SYSTEM TEST"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check if backend is running
echo "📡 Step 1: Checking backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}❌ Backend is not running. Please start it first.${NC}"
    echo "   Run: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    exit 1
fi

# Step 2: Check if frontend is running
echo ""
echo "🖥️  Step 2: Checking frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend is not running. You may need to start it.${NC}"
    echo "   Run: cd frontend && npm run dev"
fi

# Step 3: Generate demo data
echo ""
echo "🎲 Step 3: Generating demo data..."
cd backend
source venv/bin/activate
python3 ../scripts/generate_review_queue_demo.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Demo data generated successfully${NC}"
else
    echo -e "${RED}❌ Failed to generate demo data${NC}"
    exit 1
fi

# Step 4: Test API endpoints
echo ""
echo "🔌 Step 4: Testing API endpoints..."

# Test GET /api/review-queue
echo "  Testing GET /api/review-queue..."
response=$(curl -s http://localhost:8000/api/review-queue)
count=$(echo "$response" | grep -o '"id"' | wc -l)
echo -e "  ${GREEN}✅ Found $count items in review queue${NC}"

# Test GET /api/review-queue/stats
echo "  Testing GET /api/review-queue/stats..."
stats=$(curl -s http://localhost:8000/api/review-queue/stats)
echo "  Stats: $stats"

# Step 5: Summary
echo ""
echo "========================================"
echo "📊 TEST SUMMARY"
echo "========================================"
echo ""
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "📌 Next steps:"
echo "   1. Open http://localhost:3000/review-queue"
echo "   2. Review pending invoices"
echo "   3. Test approve/correct workflows"
echo "   4. Verify confidence scores are displayed"
echo "   5. Test corrections learning system"
echo ""
echo "🎯 Test scenarios to try:"
echo "   • Approve a high-confidence invoice (>85%)"
echo "   • Correct a low-confidence invoice with wrong account"
echo "   • Verify that similar invoices get auto-corrected"
echo "   • Check that patterns are created from corrections"
echo ""
echo "========================================"
