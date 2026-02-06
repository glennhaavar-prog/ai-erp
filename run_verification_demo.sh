#!/bin/bash
# Quick demo of Receipt Verification Dashboard

set -e

echo "🎯 Receipt Verification Dashboard Demo"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the ai-erp root directory"
    exit 1
fi

# Test backend API
echo "1️⃣  Testing Backend API..."
cd backend
if [ ! -d "venv" ]; then
    echo "❌ Error: Python virtual environment not found. Run setup first."
    exit 1
fi

source venv/bin/activate
python3 test_verification_api.py
if [ $? -ne 0 ]; then
    echo "❌ Backend API test failed!"
    exit 1
fi

echo ""
echo "✅ Backend API working!"
echo ""

# Instructions for running both servers
echo "2️⃣  To run the full demo:"
echo ""
echo "   Terminal 1 (Backend):"
echo "   ---------------------"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
echo "   Terminal 2 (Frontend):"
echo "   ----------------------"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "   Then open: http://localhost:3000/dashboard"
echo ""
echo "3️⃣  What you'll see:"
echo ""
echo "   🟢 Green = ALL RECEIPTS TRACKED - Nothing forgotten!"
echo "   🟡 Yellow = Few items need attention (1-3)"
echo "   🔴 Red = Items require immediate review (>3)"
echo ""
echo "   Current Status: 33 invoices, 18 booked (54.5% complete)"
echo "   Action Needed: 13 pending invoices"
echo ""
echo "✅ Demo preparation complete!"
